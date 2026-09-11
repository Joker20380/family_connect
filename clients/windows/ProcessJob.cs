using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;
namespace FamilyConnect;
internal sealed class ProcessJob:IDisposable
{
    readonly JobHandle handle;
    public ProcessJob(){
        handle=CreateJobObject(IntPtr.Zero,null);
        if(handle.IsInvalid)throw new Win32Exception(Marshal.GetLastWin32Error());
        var limits=new ExtendedLimits{Basic=new BasicLimits{LimitFlags=0x2000}};
        if(!SetInformationJobObject(handle,9,ref limits,(uint)Marshal.SizeOf<ExtendedLimits>())){
            var code=Marshal.GetLastWin32Error();handle.Dispose();throw new Win32Exception(code);
        }
    }
    public void Attach(Process process){if(!AssignProcessToJobObject(handle,process.Handle))throw new Win32Exception(Marshal.GetLastWin32Error());}
    public void Dispose()=>handle.Dispose();
    sealed class JobHandle:SafeHandleZeroOrMinusOneIsInvalid
    {
        public JobHandle():base(true){}
        protected override bool ReleaseHandle()=>CloseHandle(handle);
    }
    [StructLayout(LayoutKind.Sequential)]struct BasicLimits
    {
        public long PerProcessTime,PerJobTime;
        public uint LimitFlags;
        public UIntPtr MinWorkingSet,MaxWorkingSet;
        public uint ActiveProcessLimit;
        public UIntPtr Affinity;
        public uint Priority,Scheduling;
    }
    [StructLayout(LayoutKind.Sequential)]struct IoCounters{public ulong ReadOps,WriteOps,OtherOps,ReadBytes,WriteBytes,OtherBytes;}
    [StructLayout(LayoutKind.Sequential)]struct ExtendedLimits
    {
        public BasicLimits Basic;public IoCounters Io;
        public UIntPtr ProcessMemoryLimit,JobMemoryLimit,PeakProcessMemory,PeakJobMemory;
    }
    [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)]static extern JobHandle CreateJobObject(IntPtr security,string? name);
    [DllImport("kernel32.dll",SetLastError=true)]static extern bool SetInformationJobObject(JobHandle job,int informationClass,ref ExtendedLimits info,uint length);
    [DllImport("kernel32.dll",SetLastError=true)]static extern bool AssignProcessToJobObject(JobHandle job,IntPtr process);
    [DllImport("kernel32.dll")]static extern bool CloseHandle(IntPtr handle);
}
