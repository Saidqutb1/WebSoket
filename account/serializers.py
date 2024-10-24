from django.apps import apps
from rest_framework import serializers


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = None  # Инициализация

    def __init__(self, *args, **kwargs):
        self.Meta.model = apps.get_model('account', 'Message')
        super().__init__(*args, **kwargs)

    class Meta:
        fields = ['user', 'content', 'timestamp']