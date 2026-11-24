package android.security.keystore;
public class KeyGenParameterSpec implements java.security.spec.AlgorithmParameterSpec {
    public final String alias;
    private KeyGenParameterSpec(String alias){this.alias=alias;}
    public static class Builder {
        private final String alias;public Builder(String alias,int purposes){this.alias=alias;}
        public Builder setBlockModes(String value){return this;}public Builder setEncryptionPaddings(String value){return this;}
        public Builder setKeySize(int value){return this;}public KeyGenParameterSpec build(){return new KeyGenParameterSpec(alias);}
    }
}
