package com.familyconnect.app;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.nio.file.Path;
import java.time.ZoneId;
import java.util.HashMap;
import java.util.Locale;
import javax.xml.parsers.DocumentBuilderFactory;
import org.junit.Test;
import static org.junit.Assert.*;

public class SubscriptionPresentationTest {
    private static final long NOW=1800000000L;

    private SubscriptionPresentation.Text text(String language)throws Exception{
        String folder=language.equals("ru")?"values-ru":"values";
        Path root=Path.of(System.getProperty("fc.resources","src/main/res"));
        var document=DocumentBuilderFactory.newInstance().newDocumentBuilder().parse(root.resolve(folder).resolve("strings.xml").toFile());
        var strings=document.getElementsByTagName("string");var values=new HashMap<String,String>();
        for(int index=0;index<strings.getLength();index++){
            var element=(org.w3c.dom.Element)strings.item(index);values.put(element.getAttribute("name"),element.getTextContent());
        }
        return (name,arguments)->{assertTrue("Missing resource "+name,values.containsKey(name));return String.format(Locale.forLanguageTag(language),values.get(name),arguments);};
    }

    private JsonObject active(){
        return JsonParser.parseString("{\"confirmed_at\":1800000000,\"snapshot\":{\"effective_state\":\"active\",\"entitlement_until\":1800003600,\"paid_until\":1800003600},\"notice\":null}").getAsJsonObject();
    }

    private String render(JsonObject view,String language,boolean online,long now)throws Exception{
        return SubscriptionPresentation.summary(view,online,Locale.forLanguageTag(language),ZoneId.of("UTC"),now,text(language));
    }

    @Test public void unknownNeverSaysPaidOrActive()throws Exception{
        assertTrue(render(new JsonObject(),"en",true,NOW).contains("Device activation does not confirm payment"));
        assertTrue(render(new JsonObject(),"ru",false,NOW).contains("Нет связи"));
        assertFalse(render(new JsonObject(),"en",true,NOW).contains("Last confirmed status: Active"));
    }

    @Test public void offlineKeepsLastConfirmedStatusAndTime()throws Exception{
        String english=render(active(),"en",false,NOW),russian=render(active(),"ru",false,NOW);
        assertTrue(english.contains("Last confirmed status: Active"));assertTrue(english.contains("No connection"));
        assertTrue(russian.contains("Последнее подтверждённое состояние: Действует"));
        assertTrue(russian.contains("ошибка сети не означает отсутствие оплаты"));
        assertTrue(english.contains("Access until:"));assertTrue(english.contains("[UTC]"));
    }

    @Test public void cachedIsNotSuccessfulRefresh()throws Exception{
        assertTrue(render(active(),"en",true,NOW).contains("current status has not been checked"));
        assertTrue(render(active(),"ru",true,NOW).contains("Актуальное состояние ещё не проверено"));
    }

    @Test public void refreshOutcomesAreDistinctAndNeverInventPayment()throws Exception{
        var english=new java.util.HashSet<String>();var russian=new java.util.HashSet<String>();
        for(String outcome:new String[]{"current","unsupported","unavailable","identity_rejected","invalid","stale","busy","refreshing","cancelled"}){
            JsonObject view=active();view.addProperty("refresh_status",outcome);
            String en=render(view,"en",true,NOW),ru=render(view,"ru",true,NOW);
            english.add(en);russian.add(ru);
            assertTrue(en.contains("Last confirmed status: Active"));assertFalse(en.contains("payment received"));
            assertFalse(ru.contains("Оплачено"));
        }
        assertEquals(9,english.size());assertEquals(9,russian.size());
    }

    @Test public void nonCohortDoesNotMeanUnpaid()throws Exception{
        JsonObject view=new JsonObject();view.addProperty("cohort",false);view.addProperty("confirmed_at",NOW);
        view.addProperty("refresh_status","current");
        assertTrue(render(view,"en",true,NOW).contains("outside the paid pilot"));
        assertTrue(render(view,"ru",true,NOW).contains("Это не означает отсутствие оплаты или доступа"));
        view.addProperty("refresh_status","unavailable");
        assertTrue(render(view,"en",true,NOW).contains("not freshly confirmed"));
    }

    @Test public void exactBoundaryDoesNotRewriteBackendState()throws Exception{
        JsonObject view=active();
        assertFalse(render(view,"en",true,NOW+3599).contains("according to the device clock"));
        assertTrue(render(view,"en",true,NOW+3600).contains("according to the device clock"));
        assertEquals("active",view.getAsJsonObject("snapshot").get("effective_state").getAsString());
        assertTrue(render(view,"ru",false,NOW+3600).contains("Возможное продление здесь ещё не подтверждено"));
    }

    @Test public void endedAndGraceExplainRenewalWithoutPaymentClaim()throws Exception{
        for(String state:new String[]{"expired","grace"}){
            JsonObject view=active();view.getAsJsonObject("snapshot").addProperty("effective_state",state);
            if(state.equals("expired"))view.getAsJsonObject("snapshot").add("entitlement_until",com.google.gson.JsonNull.INSTANCE);
            assertTrue(render(view,"en",false,NOW).contains("requires renewal"));
            assertTrue(render(view,"ru",true,NOW).contains("требуется продление"));
        }
    }

    @Test public void onlyBackendNoticeProducesConfirmation()throws Exception{
        assertFalse(render(active(),"en",true,NOW).contains("extension confirmed"));
        JsonObject view=active(),notice=new JsonObject();notice.addProperty("subscription_event","renewed");view.add("notice",notice);
        assertTrue(render(view,"en",true,NOW).contains("Last backend event: Access extension confirmed"));
        assertTrue(render(view,"ru",true,NOW).contains("Сервис подтвердил продление доступа"));
        for(String kind:new String[]{"activated","confirmed","grace","expire","revoke"}){
            notice.addProperty("subscription_event",kind);
            assertFalse(SubscriptionPresentation.event(notice,text("ru")).isEmpty());
            assertFalse(SubscriptionPresentation.event(notice,text("en")).isEmpty());
        }
    }

    @Test public void expiredGraceShowsLastGrantedBoundaryNotEarlierPaidEnd()throws Exception{
        JsonObject view=active(),snapshot=view.getAsJsonObject("snapshot");
        snapshot.addProperty("effective_state","expired");snapshot.addProperty("grace_until",NOW+7200);
        snapshot.add("entitlement_until",com.google.gson.JsonNull.INSTANCE);
        for(String language:new String[]{"en","ru"}){
            String expected=SubscriptionPresentation.time(NOW+7200,Locale.forLanguageTag(language),ZoneId.of("UTC"));
            assertTrue(render(view,language,true,NOW+7200).contains(expected));
        }
    }

    @Test public void timeIncludesYearSecondsZoneAndDstOffset(){
        long before=java.time.Instant.parse("2026-10-25T00:30:00Z").getEpochSecond();
        String early=SubscriptionPresentation.time(before,Locale.ENGLISH,ZoneId.of("Europe/Brussels"));
        String late=SubscriptionPresentation.time(before+3600,Locale.ENGLISH,ZoneId.of("Europe/Brussels"));
        assertTrue(early.contains("2026, 02:30:00 +02:00 [Europe/Brussels]"));
        assertTrue(late.contains("2026, 02:30:00 +01:00 [Europe/Brussels]"));
        assertTrue(SubscriptionPresentation.time(before,Locale.forLanguageTag("ru"),ZoneId.of("Asia/Kolkata")).contains("+05:30"));
    }

    @Test public void clockRollbackIsExplicit()throws Exception{
        assertTrue(render(active(),"en",false,NOW-1).contains("Check the date and time"));
        assertTrue(render(active(),"ru",true,NOW-1).contains("Проверьте дату и время"));
    }

    @Test(expected=IllegalArgumentException.class) public void millisecondsAreRejected(){
        SubscriptionPresentation.time(NOW*1000,Locale.ENGLISH,ZoneId.of("UTC"));
    }

    @Test public void unixEpochAndPost2038UseSecondsWithoutOverflow(){
        assertEquals("01 Jan 1970, 00:00:00 Z [UTC]",SubscriptionPresentation.time(0,Locale.ENGLISH,ZoneId.of("UTC")));
        long later=java.time.Instant.parse("2040-01-01T00:00:00Z").getEpochSecond();
        assertEquals("01 Jan 2040, 00:00:00 Z [UTC]",SubscriptionPresentation.time(later,Locale.ENGLISH,ZoneId.of("UTC")));
    }
}
