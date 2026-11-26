import django.db.models.deletion
from django.db import migrations, models


def envolver_votos_existentes_en_papeleta(apps, schema_editor):
    """
    Antes de este cambio no existía el concepto de "papeleta": cada Voto
    era independiente. Para no perder los votos ya registrados (aunque
    sean de prueba), se agrupan todos los votos sueltos en una sola
    papeleta en vez de borrarlos.
    """
    Voto = apps.get_model('votos', 'Voto')
    Papeleta = apps.get_model('votos', 'Papeleta')

    votos_sin_papeleta = list(Voto.objects.filter(papeleta__isnull=True))
    if votos_sin_papeleta:
        papeleta = Papeleta.objects.create()
        for voto in votos_sin_papeleta:
            voto.papeleta = papeleta
            voto.save(update_fields=['papeleta'])


def no_hacer_nada(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('votos', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candidato',
            name='orden',
            field=models.PositiveIntegerField(
                unique=True,
                help_text='Número del candidato. Se usa tanto para el orden en la lista como para '
                           'ingresarlo en la pantalla de votación (debe ser único).',
            ),
        ),
        migrations.CreateModel(
            name='Papeleta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_hora', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddField(
            model_name='voto',
            name='papeleta',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='votos',
                to='votos.papeleta',
            ),
        ),
        migrations.RunPython(envolver_votos_existentes_en_papeleta, no_hacer_nada),
        migrations.AlterField(
            model_name='voto',
            name='papeleta',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='votos',
                to='votos.papeleta',
            ),
        ),
        migrations.DeleteModel(
            name='CodigoVotante',
        ),
    ]
