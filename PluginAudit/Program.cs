using Mutagen.Bethesda;
using Mutagen.Bethesda.Skyrim;
using System.Text.Json;
using var mod=SkyrimMod.CreateFromBinaryOverlay(args[0],SkyrimRelease.SkyrimSE);
var records=mod.EnumerateMajorRecords().ToArray();var keys=records.Select(x=>x.FormKey).ToHashSet();
var missing=new List<string>();int links=0;
foreach(var record in records)foreach(var link in record.EnumerateFormLinks()){
 var k=link.FormKey;links++;
 if(!k.IsNull && k.ModKey==mod.ModKey && !keys.Contains(k))missing.Add($"{record.EditorID} -> {k}");
}
if(records.Length!=4722 || missing.Count!=0)throw new Exception(JsonSerializer.Serialize(missing));
Console.WriteLine(JsonSerializer.Serialize(new{Reader="Mutagen SkyrimSE binary overlay",Records=records.Length,LinksChecked=links,MissingInternalLinks=missing,Masters=mod.ModHeader.MasterReferences.Select(x=>x.Master.ToString()),SkyrimExecuted=false},new JsonSerializerOptions{WriteIndented=true}));
