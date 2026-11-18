using Mutagen.Bethesda;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Binary.Parameters;
using System.Text.Json;
// v1.2.2 is the complete implementation input. No records are regenerated.
var input="work/build/v1.2.2/runtime";
var dest="work/build/v1.2.3/runtime";Directory.CreateDirectory(dest);
var mod=SkyrimMod.CreateFromBinary(Path.Combine(input,"MoreBrats.esp"),SkyrimRelease.SkyrimSE);
mod.ModHeader.Description="More Brats v1.2.3 development. Targeted arrival callback repair and 33% running tuning; appearances and departures retained. Tsoxer.";
foreach(var g in mod.Globals)if(g.EditorID=="MB_RepairBuild" || g.EditorID is "MB_ScriptBuild" or "MB_Build" or "MB_DiagAIRevision" || g.EditorID?.EndsWith("_ScriptBuild")==true || g.EditorID?.EndsWith("_Build")==true || g.EditorID?.EndsWith("_DiagAIRevision")==true)g.RawFloat=1203;
var masters=mod.ModHeader.MasterReferences.Select(x=>x.Master).ToArray();
mod.WriteToBinary(Path.Combine(dest,"MoreBrats.esp"),new BinaryWriteParameters{MastersListContent=MastersListContentOption.NoCheck,MastersListOrdering=new MastersListOrderingByLoadOrder(masters)});
Directory.CreateDirectory(Path.Combine(dest,"Seq"));File.Copy(Path.Combine(input,"Seq/MoreBrats.seq"),Path.Combine(dest,"Seq/MoreBrats.seq"),true);
using var result=SkyrimMod.CreateFromBinaryOverlay(Path.Combine(dest,"MoreBrats.esp"),SkyrimRelease.SkyrimSE);
Console.WriteLine(JsonSerializer.Serialize(new{Records=result.EnumerateMajorRecords().Count(),NPCs=result.Npcs.Count,Masters=result.ModHeader.MasterReferences.Select(x=>x.Master.ToString())}));
