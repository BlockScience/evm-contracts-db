# Generated by Django 4.1 on 2022-08-24 06:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AddressOwner",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200)),
                ("website", models.URLField(null=True)),
            ],
            options={
                "db_table": "address_owners",
            },
        ),
        migrations.CreateModel(
            name="BlockchainAddress",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "chain",
                    models.CharField(
                        choices=[
                            ("ETH", "Ethereum"),
                            ("RIN", "Rinkeby"),
                            ("ROP", "Ropsten"),
                            ("GOE", "GOERLI"),
                            ("KOV", "Kovan"),
                            ("GNO", "Gnosis"),
                            ("OPT", "Optimism"),
                            ("POL", "Polygon"),
                        ],
                        default="ETH",
                        max_length=3,
                    ),
                ),
                ("address", models.CharField(max_length=42)),
            ],
            options={
                "db_table": "blockchain_addresses",
            },
        ),
        migrations.CreateModel(
            name="BlockchainTransaction",
            fields=[
                (
                    "transaction_id",
                    models.CharField(
                        default="0.0", max_length=20, primary_key=True, serialize=False
                    ),
                ),
                ("transaction_hash", models.CharField(max_length=66, null=True)),
                ("block_number", models.PositiveIntegerField()),
                ("value", models.FloatField()),
                ("error", models.CharField(max_length=20, null=True)),
                ("call_name", models.CharField(max_length=200, null=True)),
                ("call_inputs", models.JSONField(default=dict, null=True)),
                ("call_outputs", models.JSONField(default=dict, null=True)),
                (
                    "contracts_created",
                    models.ManyToManyField(
                        related_name="created_by_transaction",
                        to="database.blockchainaddress",
                    ),
                ),
                (
                    "from_address",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="transactions_from",
                        to="database.blockchainaddress",
                    ),
                ),
                (
                    "to_address",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="transactions_to",
                        to="database.blockchainaddress",
                    ),
                ),
            ],
            options={
                "db_table": "blockchain_transactions",
            },
        ),
        migrations.CreateModel(
            name="BlockchainTransactionTrace",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("trace_address", models.CharField(default="0.0.0", max_length=50)),
                ("value", models.FloatField()),
                ("compressed_trace", models.TextField(max_length=1000, null=True)),
                ("error", models.CharField(max_length=20, null=True)),
                ("outputs", models.JSONField(default=dict, null=True)),
                (
                    "delegate",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="delegate_for_trace",
                        to="database.blockchainaddress",
                    ),
                ),
                (
                    "from_address",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="traces_from",
                        to="database.blockchainaddress",
                    ),
                ),
                (
                    "originating_from",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="traces",
                        to="database.blockchaintransaction",
                    ),
                ),
                (
                    "to_address",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="traces_to",
                        to="database.blockchainaddress",
                    ),
                ),
            ],
            options={
                "db_table": "blockchain_traces",
            },
        ),
        migrations.CreateModel(
            name="BlockchainTransactionLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("log_index", models.CharField(default="0.0.0", max_length=50)),
                ("topics", models.CharField(max_length=267, null=True)),
                ("event", models.CharField(max_length=200, null=True)),
                ("compressed_log", models.TextField(null=True)),
                (
                    "address",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="logs_from",
                        to="database.blockchainaddress",
                    ),
                ),
                (
                    "originating_from",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="logs",
                        to="database.blockchaintransaction",
                    ),
                ),
            ],
            options={
                "db_table": "blockchain_logs",
            },
        ),
        migrations.AddConstraint(
            model_name="blockchainaddress",
            constraint=models.UniqueConstraint(
                fields=("chain", "address"), name="unique_address"
            ),
        ),
        migrations.AddField(
            model_name="addressowner",
            name="blockchain_addresses",
            field=models.ManyToManyField(
                related_name="belongs_to_owner", to="database.blockchainaddress"
            ),
        ),
    ]