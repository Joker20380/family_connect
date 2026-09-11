using FamilyConnect;
using System.Text.Json;
if(Environment.GetEnvironmentVariable("GITHUB_ACTIONS")!="true")return 2;
try {
    // Synthetic CI fixture only. Production broker must generate its own validated config.
    var config=Console.ReadLine()??throw new Exception("missing fixture");
    using var engine=TcpEngine.Start(args[0],config);
    Console.WriteLine(JsonSerializer.Serialize(new{pid=engine.Id}));Console.Out.Flush();
    var command=Console.ReadLine();
    if(command is not null&&command!="stop")throw new Exception("unsupported test command");
    engine.Dispose();engine.Dispose(); // idempotent ordinary shutdown
    return 0;
}catch(Exception e){Console.Error.WriteLine(e.GetType().Name+": "+e.Message);return 1;}
