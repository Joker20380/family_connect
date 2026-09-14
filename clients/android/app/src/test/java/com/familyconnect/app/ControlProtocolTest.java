package com.familyconnect.app;
import org.junit.Test;
public class ControlProtocolTest {
    @Test public void immutableCorpus()throws Exception {
        System.out.println(ControlVectors.run(name->getClass().getClassLoader().getResourceAsStream(name)));
    }
    @Test public void strictJson()throws Exception {ControlVectors.jsonRefusals();}
}
