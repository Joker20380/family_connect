package android.util;
import java.io.*;
import java.nio.file.*;
public class AtomicFile {
    private final File file;
    public AtomicFile(File file){this.file=file;}
    public File getBaseFile(){return file;}
    public FileInputStream openRead()throws FileNotFoundException{return new FileInputStream(file);}
    public FileOutputStream startWrite()throws IOException{return new FileOutputStream(file+".new");}
    public void finishWrite(FileOutputStream output)throws IOException{output.getFD().sync();output.close();Files.move(Path.of(file+".new"),file.toPath(),StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);}
    public void failWrite(FileOutputStream output)throws IOException{output.close();Files.deleteIfExists(Path.of(file+".new"));}
}
