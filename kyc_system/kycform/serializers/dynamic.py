from rest_framework import serializers

class DynamicSPCSerializer(serializers.Serializer):
    @classmethod
    def from_columns(cls, columns):
        return type(
            "AutoSerializer",
            (cls,),
            {
                col: serializers.CharField(required=False, allow_null=True)
                for col in columns
            }
        )
