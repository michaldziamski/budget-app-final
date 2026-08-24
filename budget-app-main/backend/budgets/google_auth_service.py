import logging
from django.contrib.auth.models import User
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

logger = logging.getLogger(__name__)


class GoogleAuthService:
    """Serwis do obsługi logowania przez Google OAuth"""
    
    @staticmethod
    def verify_google_token(token: str) -> dict:
        """Weryfikuje token Google i zwraca dane użytkownika"""
        try:
            # Weryfikuj token z Google
            idinfo = id_token.verify_oauth2_token(
                token, 
                google_requests.Request(), 
                settings.GOOGLE_OAUTH2_CLIENT_ID
            )
            
            # Sprawdź czy token jest dla właściwej aplikacji
            if idinfo['aud'] != settings.GOOGLE_OAUTH2_CLIENT_ID:
                raise ValueError('Token nie jest dla tej aplikacji')
            
            return {
                'email': idinfo.get('email'),
                'first_name': idinfo.get('given_name', ''),
                'last_name': idinfo.get('family_name', ''),
                'picture': idinfo.get('picture', ''),
                'google_id': idinfo.get('sub'),
            }
        except ValueError as e:
            logger.error(f"Google token verification failed: {e}")
            raise Exception(f"Nieprawidłowy token Google: {str(e)}")
        except Exception as e:
            logger.error(f"Error verifying Google token: {e}")
            raise Exception(f"Błąd weryfikacji tokena Google: {str(e)}")
    
    @staticmethod
    def login_with_google(token: str) -> dict:
        """Loguje użytkownika przez Google (tylko dla istniejących kont)"""
        try:
            # Weryfikuj token Google
            google_user_data = GoogleAuthService.verify_google_token(token)
            
            email = google_user_data.get('email')
            if not email:
                raise Exception("Email nie został znaleziony w danych Google")
            
            # Znajdź użytkownika po emailu
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise Exception(
                    "Konto z tym adresem email nie istnieje. "
                    "Zarejestruj się najpierw przez formularz rejestracji."
                )
            
            # Sprawdź czy użytkownik jest aktywny
            if not user.is_active:
                raise Exception(
                    "Konto nie jest aktywne. Sprawdź email w celu weryfikacji adresu."
                )
            
            # Generuj tokeny JWT
            refresh = RefreshToken.for_user(user)
            
            return {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                }
            }
        except Exception as e:
            logger.error(f"Google login error: {e}")
            raise

