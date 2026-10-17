import datetime

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('secretariats', '0003_secretariat_autoriser_stock_negatif'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlageHoraire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('jour', models.PositiveSmallIntegerField(choices=[(0, 'Lundi'), (1, 'Mardi'), (2, 'Mercredi'), (3, 'Jeudi'), (4, 'Vendredi'), (5, 'Samedi'), (6, 'Dimanche')], verbose_name='jour')),
                ('ouvert', models.BooleanField(default=True, verbose_name='ouvert')),
                ('heure_debut', models.TimeField(default=datetime.time(7, 30), verbose_name="heure d'ouverture")),
                ('heure_fin', models.TimeField(default=datetime.time(19, 0), verbose_name='heure de fermeture')),
                ('secretariat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='plages_horaires', to='secretariats.secretariat')),
            ],
            options={
                'verbose_name': 'plage horaire',
                'verbose_name_plural': 'plages horaires',
                'ordering': ['secretariat', 'jour'],
            },
        ),
        migrations.CreateModel(
            name='ParametreNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('intervalle_ca_min', models.PositiveSmallIntegerField(default=120, help_text="Fréquence d'envoi du CA pendant les horaires : 60, 120, 180 ou 240 min.", verbose_name='intervalle du bilan de CA (minutes)')),
                ('alerte_ca_on', models.BooleanField(default=True, verbose_name='bilan de CA périodique activé')),
                ('alerte_stock_on', models.BooleanField(default=True, verbose_name='alerte de stock faible activée')),
                ('bilan_jour_on', models.BooleanField(default=True, verbose_name='bilan de fin de journée activé')),
                ('seuil_ecart_caisse', models.PositiveIntegerField(default=0, help_text="0 = pas d'alerte sur l'écart de caisse.", verbose_name="seuil d'alerte sur écart de caisse (XAF)")),
                ('dernier_envoi_ca', models.DateTimeField(blank=True, null=True, verbose_name='dernier bilan de CA envoyé')),
                ('dernier_bilan_jour', models.DateField(blank=True, null=True, verbose_name='dernier bilan de journée envoyé')),
                ('secretariat', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='parametre_notification', to='secretariats.secretariat')),
            ],
            options={
                'verbose_name': 'paramètre de notification',
                'verbose_name_plural': 'paramètres de notification',
            },
        ),
        migrations.AddConstraint(
            model_name='plagehoraire',
            constraint=models.UniqueConstraint(fields=('secretariat', 'jour'), name='une_plage_par_jour_et_secretariat'),
        ),
    ]
