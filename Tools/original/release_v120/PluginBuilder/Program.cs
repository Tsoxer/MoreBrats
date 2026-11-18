using Mutagen.Bethesda;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Plugins.Binary.Parameters;
using System.Text.Json;
// Direct continuation of the v1.1.0 incremental generator. The actual released
// v1.1.0 plugin is the input; all old records and reference identities survive.
var root="work/build/v1.2.0";
var dest=Path.Combine(root,"runtime");Directory.CreateDirectory(dest);
var mod=SkyrimMod.CreateFromBinary("work/v1.1.0/runtime/MoreBrats.esp",SkyrimRelease.SkyrimSE);
var sky=ModKey.FromNameAndExtension("Skyrim.esm");var hf=ModKey.FromNameAndExtension("HearthFires.esm");var db=ModKey.FromNameAndExtension("Dragonborn.esm");
FormKey F(uint id)=>new(mod.ModKey,id);
var holding=mod.Cells.SelectMany(b=>b.SubBlocks).SelectMany(b=>b.Cells).Single(c=>c.EditorID=="MB_DisabledReferenceStorage");
var refSource=holding.Persistent.OfType<PlacedNpc>().Single(n=>n.FormKey.ID==0x809);
var roster=JsonDocument.Parse(File.ReadAllText("work/release_v120/Config/appearance-roster.json")).RootElement;
var donors=roster.GetProperty("additional_donors").EnumerateArray().ToArray();
var raceNames=new[]{"Nord","Imperial","Breton","Redguard"};
foreach(var c in JsonDocument.Parse(File.ReadAllText(Path.Combine(root,"settlements.json"))).RootElement.EnumerateArray()) {
 uint oldRoot=c.GetProperty("base").GetUInt32(),newRoot=0x100000+oldRoot*16;
 string name=c.GetProperty("name").GetString()!;int max=c.GetProperty("maximum").GetInt32();
 var oldNpcs=c.GetProperty("npc_ids").EnumerateArray().Select(x=>x.GetUInt32()).ToArray();
 var quest=mod.Quests.Single(q=>q.FormKey.ID==oldRoot);
 var script=quest.VirtualMachineAdapter!.Scripts.Single();
 var refs=new FormList(F(newRoot+0x1000),SkyrimRelease.SkyrimSE){EditorID=$"MB_{name}_NamedDonorRefs"};
 foreach(var donor in donors) {
  int race=Array.IndexOf(raceNames,donor.GetProperty("Race").GetString());
  bool girl=donor.GetProperty("Gender").GetString()=="Female";
  int ordinal=donor.GetProperty("appended_donor_index").GetInt32();
  var donorKey=new FormKey(ModKey.FromNameAndExtension(donor.GetProperty("master").GetString()!),donor.GetProperty("local_id").GetUInt32());
  string donorName=donor.GetProperty("name").GetString()!.Replace(" ","").Replace("-","").Replace("'","");
  for(int clothing=0;clothing<5;clothing++) {
   int oldVariant=clothing<3?(girl?3:0)+clothing:6+(girl?2:0)+clothing-3;
   uint sourceID=race==0?oldNpcs[oldVariant]:0x20000+oldRoot+(uint)((race-1)*10+oldVariant);
   var source=mod.Npcs.Single(n=>n.FormKey.ID==sourceID);
   int appendVariant=ordinal*5+clothing;
   var npc=source.Duplicate(F(newRoot+(uint)appendVariant));
   npc.EditorID=$"MB_{name}_{donorName}Outfit{clothing}";
   // Preserve the existing template mask and all More Brats-owned gameplay data.
   npc.Template.SetTo(donorKey);mod.Npcs.Add(npc);
   for(int slot=0;slot<max;slot++) {
    var actor=refSource.Duplicate(F(newRoot+0x2000+(uint)(appendVariant*max+slot)));
    actor.EditorID=$"MB_{name}_{donorName}Slot{slot}Outfit{clothing}";actor.Base.SetTo(npc.FormKey);
    holding.Persistent.Add(actor);refs.Items.Add(actor.ToLink<ISkyrimMajorRecordGetter>());
   }
  }
 }
 mod.FormLists.Add(refs);
 var prop=new ScriptObjectProperty{Name="NamedDonorForms"};prop.Object.SetTo(refs.FormKey);script.Properties.Add(prop);
}
mod.ModHeader.Description="More Brats v1.2.0 development. Expanded vanilla child appearance donors; existing 19-settlement gameplay retained. Tsoxer.";
foreach(var g in mod.Globals)if(g.EditorID=="MB_RepairBuild" || g.EditorID is "MB_ScriptBuild" or "MB_Build" or "MB_DiagAIRevision" || g.EditorID?.EndsWith("_ScriptBuild")==true || g.EditorID?.EndsWith("_Build")==true || g.EditorID?.EndsWith("_DiagAIRevision")==true)g.RawFloat=1200;
mod.WriteToBinary(Path.Combine(dest,"MoreBrats.esp"),new BinaryWriteParameters{MastersListContent=MastersListContentOption.NoCheck,MastersListOrdering=new MastersListOrderingByLoadOrder(new[]{sky,hf,db})});
Directory.CreateDirectory(Path.Combine(dest,"Seq"));File.Copy("work/v1.1.0/runtime/Seq/MoreBrats.seq",Path.Combine(dest,"Seq/MoreBrats.seq"),true);
using var result=SkyrimMod.CreateFromBinaryOverlay(Path.Combine(dest,"MoreBrats.esp"),SkyrimRelease.SkyrimSE);
Console.WriteLine(JsonSerializer.Serialize(new{Records=result.EnumerateMajorRecords().Count(),NPCs=result.Npcs.Count,Masters=result.ModHeader.MasterReferences.Select(x=>x.Master.ToString())}));
