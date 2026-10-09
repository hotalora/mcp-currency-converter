def get_user_and_roles(ctx, allowed_roles, log_prefix="tool"):
    if ctx is None:
        print(f"Contexto MCP no disponible, omitiendo validación de roles. [{log_prefix}]")
        return None, []
    user = getattr(ctx, "user", None)
    if user is None:
        try:
            from src.applications.middleware.auth_middleware import EntraIDAuthMiddleware
            user = EntraIDAuthMiddleware.user_ctx.get()
        except Exception:
            user = None
    roles = user.get("roles", []) if user else []
    print(f"Roles en {log_prefix}: {roles}")
    if user is None:
        raise Exception("No se encontró información de usuario en el contexto MCP ni en el contextvar global")
    if not ("MCP.ADMIN" in roles or any(role in roles for role in allowed_roles)):
        raise Exception(f"No autorizado: falta el rol MCP.ADMIN o uno de {allowed_roles}")
    return user, roles