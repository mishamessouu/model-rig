from .service import NotFound


def handle(service, request):
    """Answer one request dict with a response dict, like a thin HTTP layer."""
    user = request.get("user")
    if not user:
        return {"status": 401}
    action = request.get("action")
    try:
        if action == "book":
            booking = service.book(
                user, request["room"], request["title"], int(request["hours"])
            )
            return {"status": 201, "id": booking.id}
        if action == "get":
            booking = service.get(user, int(request["id"]))
            return {"status": 200, "title": booking.title, "state": booking.status}
        if action == "cancel":
            booking = service.cancel(user, int(request["id"]))
            return {"status": 200, "state": booking.status}
        if action == "search":
            found = service.search(user, request.get("q", ""))
            return {"status": 200, "ids": [booking.id for booking in found]}
        if action == "quote":
            return {"status": 200, "price": service.quote(user, int(request["hours"]))}
    except NotFound:
        return {"status": 404}
    except (KeyError, ValueError) as error:
        return {"status": 400, "error": str(error)}
    return {"status": 400, "error": "unknown action"}
