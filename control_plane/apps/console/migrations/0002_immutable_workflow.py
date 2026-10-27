from django.db import migrations


FORWARD = """
CREATE FUNCTION cp0_immutable_record() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'CONTROL_PLANE_IMMUTABLE_RECORD';
END;
$$;
CREATE TRIGGER audit_immutable BEFORE UPDATE OR DELETE ON console_auditrecord
FOR EACH ROW EXECUTE FUNCTION cp0_immutable_record();
CREATE TRIGGER release_immutable BEFORE UPDATE OR DELETE ON console_releasemetadata
FOR EACH ROW EXECUTE FUNCTION cp0_immutable_record();
CREATE FUNCTION cp0_protect_operation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'CONTROL_PLANE_INTENT_RETAINED';
    END IF;
    IF ROW(NEW.id,NEW.device_id,NEW.action,NEW.payment_id,NEW.period_start,NEW.paid_until,
           NEW.grace_until,NEW.created_by_id,NEW.created_at) IS DISTINCT FROM
       ROW(OLD.id,OLD.device_id,OLD.action,OLD.payment_id,OLD.period_start,OLD.paid_until,
           OLD.grace_until,OLD.created_by_id,OLD.created_at) THEN
        RAISE EXCEPTION 'CONTROL_PLANE_IMMUTABLE_INTENT';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER operation_intent_immutable BEFORE UPDATE OR DELETE ON console_operationrequest
FOR EACH ROW EXECUTE FUNCTION cp0_protect_operation();
CREATE FUNCTION cp0_protect_payment() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'CONTROL_PLANE_PAYMENT_RETAINED';
    END IF;
    IF OLD.confirmed_at IS NOT NULL AND NEW IS DISTINCT FROM OLD THEN
        RAISE EXCEPTION 'CONTROL_PLANE_CONFIRMED_PAYMENT_IMMUTABLE';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER payment_confirmed_immutable BEFORE UPDATE OR DELETE ON console_paymentrecord
FOR EACH ROW EXECUTE FUNCTION cp0_protect_payment();
"""

REVERSE = """
DROP TRIGGER payment_confirmed_immutable ON console_paymentrecord;
DROP FUNCTION cp0_protect_payment();
DROP TRIGGER operation_intent_immutable ON console_operationrequest;
DROP FUNCTION cp0_protect_operation();
DROP TRIGGER release_immutable ON console_releasemetadata;
DROP TRIGGER audit_immutable ON console_auditrecord;
DROP FUNCTION cp0_immutable_record();
"""


class Migration(migrations.Migration):
    dependencies = [('console', '0001_initial')]
    operations = [migrations.RunSQL(FORWARD, REVERSE)]
