from rest_framework.throttling import ScopedRateThrottle

class SensitiveRateThrottle(ScopedRateThrottle):
    scope = "sensitive"


class AuthRateThrottle(ScopedRateThrottle):
    scope = "auth"
