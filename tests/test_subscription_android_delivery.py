from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / 'clients/android/app/src/main/java/com/familyconnect/app'


def test_confirmed_save_precedes_existing_worker_delivery_and_ui_ack():
    source = (ROOT / 'ChatRuntime.java').read_text()
    refresh = source.split('static void refreshSubscription(', 1)[1].split('static void deliverSavedNotifications(', 1)[0]
    assert refresh.index('expected.acceptSubscription(') < refresh.index('completion.accept(result)')
    assert refresh.index('completion.accept(result)') < refresh.index('getMainLooper()).post(()->deliverSavedNotifications(app))')
    assert '"current".equals(outcome)||"stale".equals(outcome)' in refresh


def test_resume_drains_only_existing_storage_without_fetch_or_activation_gate():
    source = (ROOT / 'ChatRuntime.java').read_text()
    drain = source.split('static void deliverSavedNotifications(', 1)[1].split('static JsonArray serviceEvents(', 1)[0]
    assert 'WORKER.execute(' in drain and 'ChatLocalAndroid.hasState(app)' in drain
    assert 'deliverNotifications(app,open(app,false))' in drain
    for forbidden in ('refreshSubscription', 'FriendsAccessAndroid', 'enroll(', 'schedule', 'activated'):
        assert forbidden not in drain
    resume = (ROOT / 'FriendsActivity.java').read_text().split('void onResume()', 1)[1].split('void onPause()', 1)[0]
    assert resume.index('deliverSavedNotifications(this)') < resume.index('getBoolean("activated",false)')


def test_hidden_dialog_does_not_ack_and_visible_dialog_suppresses_notification():
    source = (ROOT / 'SubscriptionUi.java').read_text()
    assert 'getDecorView().hasWindowFocus()&&saved.has("notice")' in source
    assert 'addOnWindowFocusChangeListener(focus)' in source
    assert 'removeOnWindowFocusChangeListener(focus)' in source
    assert 'else if(foregroundDialog==dialog)foregroundDialog=null' in source
    assert 'SubscriptionUi.visible()' in (ROOT / 'ChatRuntime.java').read_text()
