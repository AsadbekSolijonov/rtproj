from djangochannelsrestframework.permissions import BasePermission


class WsIsAuthenticatedOrReadOnly(BasePermission):
    READONLY_ACTIONS = {
        "connect", "list", "retrieve",
        "subscribe_to_message_activity", "unsubscribe_to_message_activity",
        "whoami",
    }

    def has_permission(self, scope, consumer, action, **kwargs):
        user = scope.get("user")
        if action in self.READONLY_ACTIONS:
            return True
        return bool(user and user.is_authenticated)
