from friendship.models import FriendshipRequest

def notification_count(request):
    """Giriş yapmış kullanıcının okunmamış arkadaşlık isteği sayısını döner.
    """
    if request.user.is_authenticated:
        # Okunmamış ve bekleyen istekleri say
        unread_requests_count = FriendshipRequest.objects.filter(
            to_user=request.user,
            viewed=False,  # friendship kütüphanesinin varsayılan olarak viewed alanı olmayabilir, kontrol etmek gerek
            accepted=False,
            rejected=False
        ).count()
        # Eğer FriendshipRequest modelinde 'viewed' alanı yoksa aşağıdaki satırı kullanın:
        # unread_requests_count = FriendshipRequest.objects.filter(
        #     to_user=request.user,
        #     accepted=False,
        #     rejected=False
        # ).count()
        return {'notification_count': unread_requests_count}
    return {'notification_count': 0} 