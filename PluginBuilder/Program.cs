using Mutagen.Bethesda;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Plugins.Binary.Parameters;
using System.Text.Json;
var root="work/build/v1.1.0";
var dest=Path.Combine(root,"runtime");Directory.CreateDirectory(dest);
var mod=SkyrimMod.CreateFromBinary("work/v1.0.0/runtime/MoreBrats.esp",SkyrimRelease.SkyrimSE);
var sky=ModKey.FromNameAndExtension("Skyrim.esm");var hf=ModKey.FromNameAndExtension("HearthFires.esm");var db=ModKey.FromNameAndExtension("Dragonborn.esm");
FormKey F(uint id)=>new(mod.ModKey,id);
var holding=mod.Cells.SelectMany(b=>b.SubBlocks).SelectMany(b=>b.Cells).Single(c=>c.EditorID=="MB_DisabledReferenceStorage");
var refSource=holding.Persistent.OfType<PlacedNpc>().Single(n=>n.FormKey.ID==0x809);
// Public Bethesda metadata + UESP NPC race/gender/base-ID tables are preserved
// separately in research/v110. FaceGen uses the same Traits inheritance as v1.0.
var raceIDs=new uint[]{0x2c659,0x2c65c,0x2c65a};
var male=new FormKey[]{new(sky,0x13359),new(hf,0x3f56),new(hf,0x403c)};
var female=new FormKey[]{new(sky,0x13bad),new(sky,0x133ab),new(sky,0x13ba9)};
var raceNames=new[]{"Imperial","Breton","Redguard"};
ScriptObjectProperty Obj(FormKey key){var p=new ScriptObjectProperty{Name=""};p.Object.SetTo(key);return p;}
foreach(var c in JsonDocument.Parse(File.ReadAllText(Path.Combine(root,"settlements.json"))).RootElement.EnumerateArray()) {
 uint oldRoot=c.GetProperty("base").GetUInt32(),newRoot=0x20000+oldRoot;
 string name=c.GetProperty("name").GetString()!;int max=c.GetProperty("maximum").GetInt32();
 var oldNpcs=c.GetProperty("npc_ids").EnumerateArray().Select(x=>x.GetUInt32()).ToArray();
 var quest=mod.Quests.Single(q=>q.FormKey.ID==oldRoot);
 var script=quest.VirtualMachineAdapter!.Scripts.Single();
 for(int race=0;race<3;race++) {
  var bases=new List<Npc>();
  for(int v=0;v<10;v++) {
   var source=mod.Npcs.Single(n=>n.FormKey.ID==oldNpcs[v]);
   var npc=source.Duplicate(F(newRoot+(uint)(race*10+v)));
   npc.EditorID=$"MB_{name}_{raceNames[race]}Variant{v}";
   bool girl=(npc.Configuration.Flags & NpcConfiguration.Flag.Female)!=0;
   npc.Race.SetTo(new FormKey(sky,raceIDs[race]));npc.Template.SetTo(girl?female[race]:male[race]);
   mod.Npcs.Add(npc);bases.Add(npc);
  }
  var prop=new ScriptObjectListProperty{Name=raceNames[race]+"Refs"};
  for(int slot=0;slot<max;slot++)for(int v=0;v<10;v++) {
   var actor=refSource.Duplicate(F(newRoot+0x100+(uint)(race*max*10+slot*10+v)));
   actor.EditorID=$"MB_{name}_{raceNames[race]}Slot{slot}Variant{v}";actor.Base.SetTo(bases[v].FormKey);
   holding.Persistent.Add(actor);prop.Objects.Add(Obj(actor.FormKey));
  }
  script.Properties.Add(prop);
 }
}
mod.ModHeader.Description="More Brats v1.1.0. Four vanilla human child races, two genders, five outfits; existing 19-settlement gameplay retained. Tsoxer.";
foreach(var g in mod.Globals)if(g.EditorID=="MB_RepairBuild" || g.EditorID is "MB_ScriptBuild" or "MB_Build" or "MB_DiagAIRevision" || g.EditorID?.EndsWith("_ScriptBuild")==true || g.EditorID?.EndsWith("_Build")==true || g.EditorID?.EndsWith("_DiagAIRevision")==true)g.RawFloat=1100;
mod.WriteToBinary(Path.Combine(dest,"MoreBrats.esp"),new BinaryWriteParameters{MastersListContent=MastersListContentOption.NoCheck,MastersListOrdering=new MastersListOrderingByLoadOrder(new[]{sky,hf,db})});
Directory.CreateDirectory(Path.Combine(dest,"Seq"));File.Copy("work/v1.0.0/runtime/Seq/MoreBrats.seq",Path.Combine(dest,"Seq/MoreBrats.seq"),true);
using var result=SkyrimMod.CreateFromBinaryOverlay(Path.Combine(dest,"MoreBrats.esp"),SkyrimRelease.SkyrimSE);
Console.WriteLine(JsonSerializer.Serialize(new{Records=result.EnumerateMajorRecords().Count(),NPCs=result.Npcs.Count,Masters=result.ModHeader.MasterReferences.Select(x=>x.Master.ToString())}));
