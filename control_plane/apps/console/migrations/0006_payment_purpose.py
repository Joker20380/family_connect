from django.core.validators import MinValueValidator
from django.db import migrations, models


FORWARD = """
CREATE FUNCTION cp0_protect_payment_purpose() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.purpose IS DISTINCT FROM OLD.purpose THEN
        RAISE EXCEPTION 'CONTROL_PLANE_PAYMENT_PURPOSE_IMMUTABLE';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER payment_purpose_immutable BEFORE UPDATE ON console_paymentrecord
FOR EACH ROW EXECUTE FUNCTION cp0_protect_payment_purpose();
"""

REVERSE = """
DROP TRIGGER payment_purpose_immutable ON console_paymentrecord;
DROP FUNCTION cp0_protect_payment_purpose();
"""


class Migration(migrations.Migration):
    dependencies = [('console', '0005_observations_immutable')]
    operations = [
        migrations.AddField(model_name='paymentrecord', name='purpose', field=models.CharField(
            choices=[('customer_payment', 'Оплата клиента'), ('internal_canary', 'Внутренняя проверка (canary)')],
            default='customer_payment', max_length=24, verbose_name='Назначение')),
        migrations.AlterField(model_name='paymentrecord', name='amount_minor', field=models.PositiveIntegerField(
            validators=[MinValueValidator(0)], verbose_name='Сумма в минимальных единицах')),
        migrations.RemoveConstraint(model_name='paymentrecord', name='positive_payment_amount'),
        migrations.AddConstraint(model_name='paymentrecord', constraint=models.CheckConstraint(
            condition=(models.Q(purpose='customer_payment', amount_minor__gt=0) |
                models.Q(purpose='internal_canary', amount_minor=0)), name='payment_purpose_amount')),
        migrations.RunSQL(FORWARD, REVERSE),
    ]
