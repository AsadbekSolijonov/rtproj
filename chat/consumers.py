from rest_framework import status
from asgiref.sync import sync_to_async
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework.mixins import ListModelMixin
from djangochannelsrestframework.decorators import action
from djangochannelsrestframework.observer import model_observer

from .models import Message
from .permissions import WsIsAuthenticatedOrReadOnly
from .serializers import MessageSerializer


class MessageConsumer(ListModelMixin, GenericAsyncAPIConsumer):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = (WsIsAuthenticatedOrReadOnly,)  # hozircha bo'sh

    # ---------- Diagnostika ----------
    @action()
    async def whoami(self, **kwargs):
        try:
            u = self.scope.get("user")
            return {
                "action": "whoami",
                "request_id": kwargs.get("request_id"),
                "is_authenticated": bool(u and u.is_authenticated),
                "username": (u.get_username() if u and u.is_authenticated else None),
            }
        except Exception as e:
            return ({"errors": [f"whoami error: {e}"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ---------- Model observer ----------
    @model_observer(Message)
    async def message_activity(self, message, **kwargs):
        # serializer qaytargan dict'ni yuboramiz
        await self.send_json(message)

    @message_activity.serializer
    def message_activity_serializer(self, instance, action, **kwargs):
        # DCRF Action ENUM -> string (msgpack/redis uchun zarur)
        try:
            action_str = action.value if hasattr(action, "value") else str(action)
        except Exception:
            action_str = str(action)

        return {
            "action": action_str,  # "create" | "update" | "delete"
            "data": {
                "id": instance.id,
                "text": instance.text,
                "created_at": instance.created_at.isoformat(),
                "user_id": instance.user_id,
                "username": instance.user.get_username() if instance.user_id else None,
            },
        }

    # ---------- Subscribe / Unsubscribe ----------
    @action()
    async def subscribe_to_message_activity(self, **kwargs):
        try:
            try:
                await self.message_activity.subscribe()
            except TypeError:
                self.message_activity.subscribe()  # ba’zi versiyalarda await emas
            return {
                "action": "subscribe_to_message_activity",
                "status": "subscribed",
                "request_id": kwargs.get("request_id"),
            }
        except Exception as e:
            return ({"errors": [f"subscribe error: {e}"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action()
    async def unsubscribe_to_message_activity(self, **kwargs):
        try:
            try:
                await self.message_activity.unsubscribe()
            except TypeError:
                self.message_activity.unsubscribe()
            return {
                "action": "unsubscribe_to_message_activity",
                "status": "unsubscribed",
                "request_id": kwargs.get("request_id"),
            }
        except Exception as e:
            return ({"errors": [f"unsubscribe error: {e}"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ---------- Yangi xabar yuborish ----------
    @action()
    async def send_message(self, data=None, **kwargs):
        """
        Frontend: {action:'send_message', request_id:'...', data:{text:'...'}}
        """
        try:
            req_id = kwargs.get("request_id")
            u = self.scope.get("user")
            if not (u and u.is_authenticated):
                return ({"errors": ["Authentication required"], "request_id": req_id},
                        status.HTTP_403_FORBIDDEN)

            payload = data or {}
            # MUHIM: ayrim DCRF versiyalarida action_kwargs dict bo'lishi shart
            ser = self.get_serializer(data=payload, action_kwargs={})
            ser.is_valid(raise_exception=True)

            obj = await sync_to_async(ser.save)(user=u)

            # ❌ qo'lda notify yo'q — observer post_save orqali o'zi yuboradi.

            resp = MessageSerializer(obj).data
            resp["request_id"] = req_id
            return (resp, status.HTTP_201_CREATED)

        except Exception as e:
            # soket yopilmasin — xatoni JSON qaytaramiz
            return ({"errors": [f"send_message error: {e}"],
                     "request_id": kwargs.get("request_id")},
                    status.HTTP_500_INTERNAL_SERVER_ERROR)
