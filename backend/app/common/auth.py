class PermissionDeniedError(Exception):
    pass


def require_role(user_roles: list[str], required_role: str) -> str:
    if required_role not in user_roles:
        raise PermissionDeniedError(f'missing role: {required_role}')
    return required_role
