from django.db import models

MAX_VOTOS_POR_PAPELETA = 7

# Cupos del directorio: los candidatos con más votos hasta esta cantidad son electos.
CUPOS_DIRECTORIO = 7


class Candidato(models.Model):
    """Cada persona/opción que aparece en la votación."""
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, help_text='Mini descripción que verán los votantes')
    foto = models.ImageField(upload_to='candidatos/', blank=True, null=True)
    orden = models.PositiveIntegerField(
        unique=True,
        help_text='Número del candidato. Se usa tanto para el orden en la lista como para '
                   'ingresarlo en la pantalla de votación (debe ser único).',
    )

    class Meta:
        ordering = ['orden', 'nombre']

    def __str__(self):
        return f'{self.orden} - {self.nombre}'


class Papeleta(models.Model):
    """
    Una ronda de votación: el operador ingresa los candidatos que un
    participante eligió (entre 1 y MAX_VOTOS_POR_PAPELETA) en un solo registro.
    """
    fecha_hora = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Papeleta #{self.id} - {self.fecha_hora:%d-%m-%Y %H:%M:%S}'


class Voto(models.Model):
    """Un voto registrado, parte de una papeleta, para un candidato."""
    papeleta = models.ForeignKey(Papeleta, on_delete=models.CASCADE, related_name='votos')
    candidato = models.ForeignKey(Candidato, on_delete=models.CASCADE, related_name='votos')
    fecha_hora = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Voto para {self.candidato.nombre} - {self.fecha_hora:%d-%m-%Y %H:%M}'


class EstadoVotacion(models.Model):
    """
    Fila única (singleton) que indica si la votación ya se cerró. Se usa
    para que la pantalla de resultados en vivo muestre las fotos de los
    7 electos en vez de solo el conteo en progreso.
    """
    cerrada = models.BooleanField(default=False)
    fecha_cierre = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Estado de la votación'
        verbose_name_plural = 'Estado de la votación'

    def __str__(self):
        return 'Cerrada' if self.cerrada else 'Abierta'

    @classmethod
    def actual(cls):
        estado, _ = cls.objects.get_or_create(pk=1)
        return estado
