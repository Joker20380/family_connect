package android.content;

import java.io.File;

public final class Context {
    private final File directory;
    public Context(File directory) { this.directory = directory; }
    public Context getApplicationContext() { return this; }
    public File getNoBackupFilesDir() { return directory; }
}
