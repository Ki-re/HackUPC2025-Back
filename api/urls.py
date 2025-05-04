from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BuscarPaisGrupoView
from .views import (
    PartyViewSet, UserViewSet, PreferenceViewSet,
    SuggestedDestinationViewSet, VoteViewSet,
    GenerateDestinationsView, VoteResultView,
    CityInfoAPIView,BuscarPaisGrupoView,CityImageAPIView, 
    ObtenerCodigoIATAView,ObtenerVuelosPartyView,
)

router = DefaultRouter()

router.register(r'parties', PartyViewSet)
router.register(r'users', UserViewSet)
router.register(r'preferences', PreferenceViewSet, basename='preference')
router.register(r'destinations', SuggestedDestinationViewSet, basename='destination')
router.register(r'votes', VoteViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('destinations/generate/', GenerateDestinationsView.as_view(), name='generate-destinations'),
    path('votes/result/', VoteResultView.as_view(), name='vote-results'),
    path('vuelos-party/', ObtenerVuelosPartyView.as_view(), name='vuelos-party'),
    path('api/iata/<str:ciudad>/', ObtenerCodigoIATAView.as_view(), name='codigo-iata'),
    path('buscarpaisgrupo/<int:party_id>/', BuscarPaisGrupoView.as_view(), name='buscar-pais-grupo'),
    path('city-image/', CityImageAPIView.as_view(), name='city-image'), 
]
