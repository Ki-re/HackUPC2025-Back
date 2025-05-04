# api/views.py

import random
import google.generativeai as genai
import string
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from .gemini_utils import obtener_codigo_iata
from rest_framework.generics import RetrieveUpdateAPIView
from .models import Party, User, Preference, SuggestedDestination, Vote
from .serializers import (
    PartySerializer, UserSerializer, PreferenceSerializer,
    SuggestedDestinationSerializer, VoteSerializer
)
from .gemini_utils import obtener_codigo_iata
from dotenv import load_dotenv
import os

# Utility to generate random 8-character party code
def generate_party_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# Party ViewSet
class PartyViewSet(viewsets.ModelViewSet):
    queryset = Party.objects.all()
    serializer_class = PartySerializer
    lookup_field = 'code'
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['code'] = generate_party_code()
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='code/(?P<code>[^/.]+)')
    def get_by_code(self, request, code=None):
        party = get_object_or_404(Party, code=code)
        serializer = self.get_serializer(party)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='users')
    def users(self, request, pk=None):
        party = self.get_object()
        users = User.objects.filter(party=party)
        return Response(UserSerializer(users, many=True).data)

# User ViewSet
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

# Preference
class PreferenceViewSet(viewsets.ViewSet):
    """
    /api/preferences/           → POST   crear o actualizar
    /api/preferences/{user_id}/ → GET    consultar
    /api/preferences/{user_id}/ → PATCH  modificar parcialmente
    """

    def list(self, request):
        """
        GET /api/preferences/
        """
        prefs = Preference.objects.all()
        serializer = PreferenceSerializer(prefs, many=True)
        return Response(serializer.data)

    def create(self, request):
        data = request.data.copy()
        user_id = data.pop('user', None)
        if not user_id:
            return Response(
                {"user": ["Este campo es obligatorio."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1) Obtener la instancia de User, o 404 si no existe
        user = get_object_or_404(User, pk=user_id)

        # 2) Usar update_or_create con la instancia y sin el campo user en defaults
        pref, created = Preference.objects.update_or_create(
            user=user,
            defaults=data
        )

        # 3) Serializar y devolver
        serializer = PreferenceSerializer(pref)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

    def retrieve(self, request, pk=None):
        preference = get_object_or_404(Preference, user__id=pk)
        serializer = PreferenceSerializer(preference)
        return Response(serializer.data)

    def partial_update(self, request, pk=None):
        preference = get_object_or_404(Preference, user__id=pk)
        serializer = PreferenceSerializer(preference, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

# SuggestedDestination generate endpoint
class GenerateDestinationsView(APIView):
    def post(self, request):
        # Placeholder IA logic
        party_id = request.data.get('party_id')
        if not party_id:
            return Response({"error": "party_id required"}, status=400)

        # Dummy destinations
        suggestions = [
            {"name": "Barcelona", "country": "Spain"},
            {"name": "Lisbon", "country": "Portugal"},
            {"name": "Rome", "country": "Italy"}
        ]

        created = []
        for s in suggestions:
            obj, _ = SuggestedDestination.objects.get_or_create(
                party_id=party_id,
                name=s['name'],
                defaults={"country": s['country']}
            )
            created.append(obj)

        return Response(SuggestedDestinationSerializer(created, many=True).data)

class SuggestedDestinationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SuggestedDestinationSerializer
    def get_queryset(self):
        party_id = self.request.query_params.get('party_id')
        return SuggestedDestination.objects.filter(party_id=party_id) if party_id else SuggestedDestination.objects.none()

# Votes
class VoteViewSet(viewsets.ModelViewSet):
    serializer_class = VoteSerializer
    queryset = Vote.objects.all()

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        party_id = self.request.query_params.get('party_id')
        if user_id and party_id:
            return Vote.objects.filter(user_id=user_id, destination__party_id=party_id)
        return Vote.objects.all()

class VoteResultView(APIView):
    def get(self, request):
        party_id = request.query_params.get('party_id')
        if not party_id:
            return Response({"error": "party_id required"}, status=400)

        results = (
            Vote.objects
            .filter(destination__party_id=party_id)
            .values("destination__name")
            .annotate(total=Count("vote", filter=Q(vote=True)))
            .order_by("-total")
        )
        return Response(results)

class CityInfoAPIView(APIView):
    """
    Endpoint para obtener información de una ciudad usando obtener_codigo_iata().
    """

    def get(self, request):
        city = request.query_params.get("city")
        if not city:
            return Response(
                {"detail": "Parámetro 'city' obligatorio"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            data = obtener_codigo_iata(city)
        except Exception as e:
            return Response(
                {"detail": f"Error al obtener datos: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY
            )

        return Response(data, status=status.HTTP_200_OK)
    
class BuscarPaisGrupoView(APIView):
    """
    GET /api/buscarpaisgrupo/{party_id}/
    Usa los datos de todos los usuarios de la party para generar
    una recomendación grupal de país.
    """

    def get(self, request, party_id=None):
        # 1) Recuperar party y usuarios
        party = get_object_or_404(Party, pk=party_id)
        users = User.objects.filter(party=party)

        # Buscar cualquier usuario con fechas válidas
        if not users.exists():
            return Response({"detail": "La party no tiene usuarios."}, status=404)

        model = genai.GenerativeModel("gemini-2.0-flash-lite")

        ubicaciones = []
        presupuestos_str = []
        preferencias = []

        for user in users:
            ubicaciones.append(user.city)

            # Presupuesto individual
            if user.budget:
                presupuestos_str.append(f"{user.name}: {user.budget}€")

            # Preferencias
            try:
                pref = Preference.objects.get(user=user)
                preferencias.append({
                    "green_travel": pref.green_travel,
                    "culture": pref.culture,
                    "food": pref.food,
                    "outdoors": pref.outdoors,
                    "weather": pref.weather,
                    "events": pref.events,
                })
            except Preference.DoesNotExist:
                continue

        if not preferencias:
            return Response({"detail": "No hay preferencias definidas."}, status=400)

        # Cadenas útiles
        ubic_str = ", ".join(set(ubicaciones))
        presupuestos_info = "\n".join(presupuestos_str)

        # Promediar preferencias
        def promedio(campo):
            return round(sum(p[campo] for p in preferencias) / len(preferencias), 2)

        # Prompt para Gemini
        prompt = f"""
Somos un grupo de {len(users)} amigos que queremos viajar juntos.
Vivimos en las siguientes ciudades: {ubic_str}.

Nuestras preferencias colectivas son:
- Turismo sostenible: {"sí" if any(p["green_travel"] for p in preferencias) else "no"}
- Cultura: {promedio("culture")} / 5
- Gastronomía: {promedio("food")} / 5
- Actividades al aire libre: {promedio("outdoors")} / 5
- Clima: {promedio("weather")} / 5
- Eventos y festivales: {promedio("events")} / 5

Recomiéndanos una única ciudad a la que todos podamos viajar y que encaje con este perfil,
teniendo en cuenta que algunas personas tienen más presupuesto que otras.
Devuélveme únicamente el nombre de la ciudad en inglés y sin explicaciones.
""".strip()

        # Llamada a Gemini
        try:
            response = model.generate_content(prompt)
            pais = response.text.strip()
        except Exception as e:
            return Response({"detail": f"Error al generar con Gemini: {e}"}, status=502)

        return Response({
            "pais_recomendado": pais,
            "prompt_enviado": prompt
        }, status=200)

class ObtenerCodigoIATAView(APIView):
    def get(self, request, ciudad=None):
        if not ciudad:
            return Response({"error": "Debes proporcionar una ciudad."}, status=400)

        codigo = obtener_codigo_iata(ciudad)

        if not codigo:
            return Response({"error": "No se pudo obtener el código IATA."}, status=500)

        return Response({
            "ciudad": ciudad,
            "codigo_iata": codigo
        }, status=200)


from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Party, User, Informacion
from .gemini_utils import obtener_codigo_iata
from .vuelos_utils import ObtainFlights

class ObtenerVuelosPartyView(APIView):
    def post(self, request):
        data = request.data
        party_id = data.get("party_id")
        adults = data.get("adults", 1)

        if not party_id:
            return Response({"detail": "Debes proporcionar un party_id."}, status=400)

        party = get_object_or_404(Party, pk=party_id)
        users = User.objects.filter(party=party)
        host = party.host

        if not users.exists():
            return Response({"detail": "No hay usuarios en la party."}, status=404)

        if not host or not host.dateDeparture or not host.dateArrival:
            return Response({"detail": "El host no tiene fechas definidas."}, status=400)

        try:
            info = Informacion.objects.get(party=party)
            pais_destino = info.pais_recomendado
        except Informacion.DoesNotExist:
            return Response({"detail": "No se ha calculado aún el país recomendado para esta party."}, status=404)

        # Convertir el país destino a IATA
        iata_destino = obtener_codigo_iata(pais_destino)

        if not iata_destino:
            return Response({"detail": f"No se pudo obtener IATA para {pais_destino}."}, status=500)

        vuelos_por_usuario = []

        for user in users:
            ciudad_origen = user.city
            iata_origen = obtener_codigo_iata(ciudad_origen)

            if not iata_origen:
                vuelos_por_usuario.append({
                    "usuario": user.name,
                    "error": f"No se pudo obtener IATA para ciudad '{ciudad_origen}'"
                })
                continue

            try:
                vuelos = ObtainFlights(
                    market="ES",
                    locale="es-ES",
                    currency="EUR",
                    airportDeparture=iata_origen,
                    airportArrival=iata_destino,
                    dateDeparture=str(host.dateDeparture),
                    dateArrival=str(host.dateArrival),
                    adults=adults
                )
                vuelos_por_usuario.append({
                    "usuario": user.name,
                    "iata_origen": iata_origen,
                    "iata_destino": iata_destino,
                    "vuelos": vuelos
                })
            except Exception as e:
                vuelos_por_usuario.append({
                    "usuario": user.name,
                    "error": str(e)
                })

        return Response({
            "pais_destino": pais_destino,
            "vuelos": vuelos_por_usuario
        }, status=200)

        
import requests

# Tu clave de Pexels
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")


class CityImageAPIView(APIView):
    """
    GET /api/city-image/?city={ciudad}
    Devuelve la URL de una imagen de la ciudad usando Pexels.
    """

    def get(self, request):
        city = request.query_params.get('city')
        if not city:
            return Response(
                {"detail": "Parámetro 'city' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST
            )

        url = 'https://api.pexels.com/v1/search'
        headers = {
            'Authorization': PEXELS_API_KEY
        }
        params = {
            'query': city,
            'per_page': 1
        }

        try:
            resp = requests.get(url, headers=headers, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            photos = data.get('photos', [])
            if not photos:
                return Response(
                    {"detail": "No se encontraron imágenes."},
                    status=status.HTTP_404_NOT_FOUND
                )
            # Obtener URL de tamaño medio (puedes elegir original, large, etc.)
            image_url = photos[0]['src']['medium']
            return Response({"url": image_url}, status=status.HTTP_200_OK)

        except requests.RequestException as e:
            return Response(
                {"detail": f"Error al llamar a Pexels: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY
            )
