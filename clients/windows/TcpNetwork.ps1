$ErrorActionPreference='Stop'
$p=[Console]::In.ReadToEnd() | ConvertFrom-Json
if($p.adapter -notmatch '^fctcp[0-9a-f]{8}$'){throw 'invalid adapter'}
$test=$p.test -eq $true
$dns=if($test){'198.18.0.1'}else{'1.1.1.1'}
$namespace=if($test){'.fctcp-ci.invalid'}else{'.'}
$routes=if($test){@('198.18.0.1/32','fd79:fc::1/128')}else{@('0.0.0.0/1','128.0.0.0/1','::/1','8000::/1')}
$local4=if($test){'198.18.0.2'}else{'10.79.0.2'}
$local6='fd79:fc::2'
$label='FamilyConnect TCP '+$p.adapter
function Adapter {Get-NetAdapter -Name $p.adapter -IncludeHidden -ErrorAction SilentlyContinue}
switch($p.operation){
 'preflight' {
  if(Adapter){throw 'adapter exists'}
  foreach($prefix in $routes){if(Get-NetRoute -DestinationPrefix $prefix -ErrorAction SilentlyContinue){throw 'route conflict'}}
  $policies=@(Get-DnsClientNrptPolicy -Effective)
  $rules=@(Get-DnsClientNrptRule)
  if(!$test -and ($policies.Count -gt 0 -or $rules.Count -gt 0)){throw 'existing DNS policy'}
  if($test -and ($rules | Where-Object {$_.Namespace -contains $namespace})){throw 'test DNS policy conflict'}
  if($test){$uplink=(Get-NetIPAddress -IPAddress '127.0.0.1' -AddressFamily IPv4).InterfaceAlias}
  else {
   $route=Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Where-Object {$_.InterfaceAlias -notlike 'fctcp*'} | Sort-Object @{Expression={$_.RouteMetric+$_.InterfaceMetric}} | Select-Object -First 1
   if(!$route){throw 'no uplink'}
   $uplink=$route.InterfaceAlias
  }
  @{uplink=$uplink} | ConvertTo-Json -Compress
 }
 'apply' {
  $deadline=[DateTime]::UtcNow.AddSeconds(20)
  do{$adapter=Adapter;if($adapter){break};Start-Sleep -Milliseconds 200}while([DateTime]::UtcNow -lt $deadline)
  if(!$adapter){throw 'adapter not ready'}
  $index=$adapter.ifIndex
  $metric=if($test){5000}else{5}
  Set-NetIPInterface -InterfaceIndex $index -AddressFamily IPv4 -Dhcp Disabled -InterfaceMetric $metric -NlMtuBytes 1280
  Set-NetIPInterface -InterfaceIndex $index -AddressFamily IPv6 -InterfaceMetric $metric -NlMtuBytes 1280
  New-NetIPAddress -InterfaceIndex $index -IPAddress $local4 -PrefixLength 32 -PolicyStore ActiveStore | Out-Null
  New-NetIPAddress -InterfaceIndex $index -IPAddress $local6 -PrefixLength 128 -PolicyStore ActiveStore | Out-Null
  foreach($prefix in $routes){
   $hop=if($prefix.Contains(':')){'::'}else{'0.0.0.0'}
   New-NetRoute -InterfaceIndex $index -DestinationPrefix $prefix -NextHop $hop -RouteMetric 5 -PolicyStore ActiveStore | Out-Null
  }
  Set-DnsClient -InterfaceIndex $index -RegisterThisConnectionsAddress $false
  Set-DnsClientServerAddress -InterfaceIndex $index -ServerAddresses @($dns)
  if(Get-DnsClientNrptRule | Where-Object {$_.DisplayName -eq $label}){throw 'DNS rule exists'}
  Add-DnsClientNrptRule -Namespace $namespace -NameServers $dns -DisplayName $label | Out-Null
  $deadline=[DateTime]::UtcNow.AddSeconds(15)
  do {
   $addresses=@(Get-NetIPAddress -InterfaceIndex $index | Where-Object {$_.IPAddress -in @($local4,$local6)})
   if($addresses.Count -eq 2 -and !($addresses | Where-Object {$_.AddressState -ne 'Preferred'})){break}
   Start-Sleep -Milliseconds 200
  }while([DateTime]::UtcNow -lt $deadline)
  if($addresses.Count -ne 2 -or ($addresses | Where-Object {$_.AddressState -ne 'Preferred'})){throw 'address not usable'}
  @{ready=$true} | ConvertTo-Json -Compress
 }
 'cleanup' {
  foreach($rule in @(Get-DnsClientNrptRule | Where-Object {$_.DisplayName -eq $label})){
   if(@($rule.Namespace).Count -ne 1 -or @($rule.Namespace)[0] -ne $namespace -or $rule.NameServers -ne $dns){throw 'DNS rule ownership conflict'}
   Remove-DnsClientNrptRule -Name $rule.Name -Force
  }
  $adapter=Adapter
  if($adapter){
   $index=$adapter.ifIndex
   foreach($prefix in $routes){Get-NetRoute -InterfaceIndex $index -DestinationPrefix $prefix -ErrorAction SilentlyContinue | Remove-NetRoute -Confirm:$false}
   Get-NetIPAddress -InterfaceIndex $index -ErrorAction SilentlyContinue | Where-Object {$_.IPAddress -in @($local4,$local6)} | Remove-NetIPAddress -Confirm:$false
   Set-DnsClientServerAddress -InterfaceIndex $index -ResetServerAddresses
  }
  $deadline=[DateTime]::UtcNow.AddSeconds(15)
  while((Adapter) -and [DateTime]::UtcNow -lt $deadline){Start-Sleep -Milliseconds 200}
  if(Adapter){throw 'adapter remains'}
  @{clean=$true} | ConvertTo-Json -Compress
 }
 default {throw 'invalid operation'}
}
exit 0
