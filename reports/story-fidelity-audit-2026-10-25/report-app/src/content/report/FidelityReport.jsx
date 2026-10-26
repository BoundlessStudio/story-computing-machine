import React, { useMemo, useRef, useState } from "react";
import { DataComponent, DataTable, EvidenceChart, MetricCard, ReportSection, RichNarrative, useDataApp } from "../../data-app-public.jsx";
import "./fidelity-report.css";

const num = (v) => v == null ? "—" : Number(v).toFixed(2);
const pct = (v) => v == null ? "—" : `${Math.round(v * 100)}%`;
const stageName = (v) => v === "outline" ? "Outline / plan" : "Final prose";
const order = { "Would restart":0, "Partial evidence":1, "API error":2, "Needs judgment":3, "Would proceed":4, "Unavailable":5, "Pending":6 };
const columns = [
  {field:"title",label:"Story",presentation:"identity",secondaryField:"slug"},
  {field:"stage",label:"Stage",renderCell:stageName}, {field:"status",label:"Outcome",presentation:"status"},
  {field:"score",label:"Score / 4",renderCell:num}, {field:"minimum_confidence",label:"Min. confidence",renderCell:pct}, {field:"reference_count",label:"Images"},
];
const stageColumns = [
  {field:"stage",label:"Stage"},{field:"scored",label:"Scored"},{field:"would_proceed",label:"Proceed"},{field:"would_restart",label:"Restart"},
  {field:"needs_judgment",label:"Judgment"},{field:"partial_evidence",label:"Partial"},{field:"unavailable",label:"Missing"},{field:"api_error",label:"Errors"},{field:"pending",label:"Pending"},
];
function Select({label,value,onChange,options}) {
  return <label className="audit-filter"><span>{label}</span><select aria-label={label} value={value} onChange={(e)=>onChange(e.target.value)}>{options.map(([v,t])=><option key={v} value={v}>{t}</option>)}</select></label>;
}

export function ReportContent() {
  const {snapshot,appTitle,canEdit,mode,setAppTitle,visible}=useDataApp();
  const rows=snapshot.queries.artifacts.rows, packages=snapshot.queries.packages.rows;
  const summaryRows=snapshot.queries.summary.rows, s=summaryRows[0];
  const stages=snapshot.queries.stages.rows, histogram=snapshot.queries.confidence.rows;
  const [search,setSearch]=useState(""), [stage,setStage]=useState("all"), [status,setStatus]=useState("all"), [images,setImages]=useState("all"), [scoreFilter,setScoreFilter]=useState("all"), [selectedId,setSelectedId]=useState(null);
  const detailRef=useRef(null);
  const filtered=useMemo(()=>rows.filter(r=>
    (stage==="all"||r.stage===stage)&&(status==="all"||r.status===status)&&
    (images==="all"||(images==="with"?r.reference_count>0:images==="missing"?r.missing_references.length>0:r.reference_count===0))&&
    (scoreFilter==="all"||(r.score!=null&&(scoreFilter==="low"?r.score<3:r.score>=3)))&&`${r.title} ${r.slug}`.toLowerCase().includes(search.toLowerCase())
  ).sort((a,b)=>order[a.status]-order[b.status]||(a.stage===b.stage?0:a.stage==="final"?-1:1)||(a.score??99)-(b.score??99)||a.title.localeCompare(b.title)),[rows,stage,status,images,scoreFilter,search]);
  const displayRows=filtered.map(({id,slug,title,stage,status,score,minimum_confidence,reference_count})=>({id,slug,title,stage,status,score,minimum_confidence,reference_count}));
  const selected=rows.find(r=>r.id===selectedId), pack=selected&&packages.find(p=>p.slug===selected.slug);
  const distributions=(selected?.response?.answers??[]).filter(a=>a.type==="score").map(a=>({dimension:a.name.replaceAll("_"," "),score:a.score,confidence:a.confidence,...Object.fromEntries(a.probabilities.map(p=>[`p${p.value}`,p.probability]))}));
  const distributionColumns=[{field:"dimension",label:"Dimension"},{field:"score",label:"Score / 4",renderCell:num},{field:"confidence",label:"Confidence",renderCell:pct},...[0,1,2,3,4].map(i=>({field:`p${i}`,label:`P(level ${i})`,renderCell:pct}))];
  const change=setter=>value=>{setter(value);setSelectedId(null);};
  const headline=s.pending===0?"Every evaluated artifact would pause for review":`${s.api_results} evaluations recorded; audit in progress`;

  return <article className="report-content fidelity-report" aria-label="Story fidelity audit">
    <header className="report-hero">
      <h1 data-data-app-title contentEditable={canEdit&&mode==="edit"} suppressContentEditableWarning onBlur={canEdit&&mode==="edit"?e=>setAppTitle(e.currentTarget.textContent.trim()||appTitle):undefined}>{appTitle}</h1>
      <RichNarrative id="audit:deck" className="report-deck" value="A retrospective check of saved outlines and prose against their full writing requests and original reference images. Story files and production restart state are unchanged." />
    </header>
    {visible("audit-summary")&&<ReportSection id="audit-summary" title={headline} queryId="summary" sourceRows={summaryRows} showHeading={false}>
      <RichNarrative id="audit:main-finding" value={`## ${headline}\n\n${s.api_results} of ${s.available_artifacts} available artifacts were evaluated across ${s.stories} stories. **${s.confidence_below_threshold} have minimum confidence below 0.80.** Under your rule, uncertainty takes priority over a low score: ${s.proceed} would proceed and ${s.restart} would automatically restart.\n\n${s.raw_below_threshold} raw scores fall below 3/4. These are tentative review signals, not established failures. Native model confidence has not been calibrated as judgment accuracy.`}/>
    </ReportSection>}
    <div className="audit-facts" aria-label="Audit coverage">
      <MetricCard id="audit-evaluated" title="Artifacts evaluated" queryId="summary" sourceRows={summaryRows} displayRows={summaryRows} value={`${s.api_results} / ${s.available_artifacts}`} description="267 outlines or plans and 268 prose files available."/>
      <MetricCard id="audit-confidence" title="Median minimum confidence" queryId="summary" sourceRows={summaryRows} displayRows={summaryRows} value={pct(s.median_confidence)} description="Automatic action requires at least 80% in every dimension."/>
      <MetricCard id="audit-images" title="Original reference images" queryId="summary" sourceRows={summaryRows} displayRows={summaryRows} value={s.original_images} description={`${s.image_packages} packages; ${s.image_evaluations} image inclusions across both stages.`}/>
    </div>
    {visible("stage-coverage")&&<DataComponent id="stage-coverage" title="Coverage and checkpoint outcomes" queryId="stages" kind="table" displayRows={stages} sourceRows={stages}>
      <DataTable rows={stages} columns={stageColumns} searchable={false} label="Outcomes by stage" compactNumbers={false}/>
    </DataComponent>}
    {visible("confidence-distribution")&&<EvidenceChart id="confidence-distribution" queryId="confidence" title="The confidence gate blocks every scored artifact" spec={{type:"bar",x:"confidence_band",y:"artifacts",valueDecimals:0}} rows={histogram} sourceRows={histogram} height={300} description="Artifacts grouped by their lowest native confidence. Automatic action requires 80% or more."/>}
    {visible("audit-gaps")&&<ReportSection id="audit-gaps" title="Source gaps and scope" queryId="packages" sourceRows={packages.filter(p=>["after-the-party","a-seat-for-the-sun","the-first-year","the-old-percentage"].includes(p.slug))} showHeading={false}>
      <RichNarrative id="audit:gaps" value={`## Source gaps and scope\n\n- **After the Party:** no saved outline or plan. Its prose was evaluated; the outline remains unavailable.\n- **A Seat for the Sun:** the prompt names an original image that is absent. Both text evaluations are marked **Partial evidence**; neither establishes visual fidelity.\n- **The First Year:** the request includes an edit to a generated table sheet. The prompt expressly excludes it as a story reference; this audit checks prose and outline, not whether that art edit was completed.\n- **The Old Percentage:** the prompt requires continuity with *Nobody Spends Her Name*. The checkpoint received the prompt's continuity description; it did not expand the linked earlier prose. Full continuity fidelity remains unverified. The raw score does not establish why it was marked down.\n\nSaved originals were sent as image bytes. Generated covers and other generated art were excluded from evaluation authority.`}/>
    </ReportSection>}
    {visible("audit-results")&&<DataComponent id="audit-results" title="Review every outline and prose file" queryId="artifacts" kind="table" displayRows={displayRows} sourceRows={filtered} description="Select a row to inspect its prompt, full text, probabilities, and reference previews. Review order: outcome, final prose first, then raw score. Low scores remain uncertain.">
      <div className="audit-controls" aria-label="Artifact filters">
        <label className="audit-filter audit-search"><span>Search stories</span><input type="search" aria-label="Search stories" value={search} onChange={e=>change(setSearch)(e.target.value)} placeholder="Title or package name"/></label>
        <Select label="Stage" value={stage} onChange={change(setStage)} options={[["all","Both stages"],["outline","Outline / plan"],["final","Final prose"]]}/>
        <Select label="Outcome" value={status} onChange={change(setStatus)} options={[["all","All outcomes"],...Object.keys(order).map(v=>[v,v])]}/>
        <Select label="References" value={images} onChange={change(setImages)} options={[["all","All packages"],["with","Saved images"],["without","No saved images"],["missing","Missing original"]]}/>
        <Select label="Raw score" value={scoreFilter} onChange={change(setScoreFilter)} options={[["all","Any / unavailable"],["low","Below 3/4"],["high","At least 3/4"]]}/>
        <button className="audit-reset" onClick={()=>{setSearch("");setStage("all");setStatus("all");setImages("all");setScoreFilter("all");setSelectedId(null);}}>Reset filters</button>
      </div>
      <p className="audit-scope" data-reviewed-rows>{filtered.length} of {rows.length} requested stage slots shown.</p>
      <DataTable rows={displayRows} columns={columns} searchable={false} rowKey="id" selectedRowKey={selectedId} label="Story fidelity results" compactNumbers={false} onRowSelect={r=>{setSelectedId(r.id);setTimeout(()=>detailRef.current?.scrollIntoView({behavior:"smooth",block:"start"}),0);}} rowActionLabel={r=>`Inspect ${r.title}, ${stageName(r.stage)}`}/>
    </DataComponent>}
    <div ref={detailRef} className="audit-detail-anchor">
      {selected&&visible("audit-detail")&&<DataComponent id="audit-detail" title={`${selected.title} · ${stageName(selected.stage)}`} queryId="artifacts" queryIds={["artifacts","packages"]} sourceRowsByQuery={{artifacts:[selected],packages:[pack]}} displayRows={[selected]} kind="table">
        <div data-reviewed-rows>
          <dl className="audit-detail-facts"><div><dt>Outcome</dt><dd>{selected.status}</dd></div><div><dt>Checkpoint score</dt><dd>{num(selected.score)} / 4</dd></div><div><dt>Minimum confidence</dt><dd>{pct(selected.minimum_confidence)}</dd></div><div><dt>Saved layout</dt><dd>{selected.layout}</dd></div></dl>
          <p className="audit-path">{selected.candidate_path}</p><ul>{selected.reasons.map((r,i)=><li key={i}>{r}</li>)}</ul>
          {distributions.length>0&&<DataTable rows={distributions} columns={distributionColumns} searchable={false} label="Native scores and probability distributions" compactNumbers={false}/>}
          <p>Material violation probability: <strong>{pct(selected.material_violation_probability)}</strong> · Source ambiguity probability: <strong>{pct(selected.source_ambiguity_probability)}</strong></p>
          <p className="audit-rubric">Levels: 0 Unfaithful · 1 Mostly missed · 2 Partly faithful · 3 Faithful · 4 Fully faithful. The API did not return a passage-level critique.</p>
          {selected.missing_references.length>0&&<p>Unavailable originals: {selected.missing_references.join(", ")}</p>}
          {pack.external_text_references?.length>0&&<p>Linked continuity text was named in the prompt but not expanded for this checkpoint: {pack.external_text_references.join(", ")}. Full continuity fidelity remains unverified.</p>}
          {pack.reference_files.length>0&&<div className="audit-reference-grid">{pack.reference_files.map(ref=><figure key={ref.path}>
            {ref.preview_data_url&&<img src={ref.preview_data_url} alt={`Saved reference: ${ref.path.split("/").at(-1)}`} loading="lazy"/>}
            <figcaption>{ref.path.split("/").at(-1)}<small>Report preview; original bytes were used for scoring.</small></figcaption>
          </figure>)}</div>}
          <details><summary>Read the full saved writing request</summary><pre className="audit-source-text">{pack.prompt_text}</pre></details>
          <details><summary>Read the complete {stageName(selected.stage).toLowerCase()}</summary><pre className="audit-source-text">{selected.candidate_text??"No saved artifact is available."}</pre></details>
          <details><summary>Inspect native API answers and source identifiers</summary><pre className="audit-source-text">{JSON.stringify({candidate_path:selected.candidate_path,candidate_sha256:selected.candidate_sha256,request_sha256:selected.request_sha256,response:selected.response,reference_files:pack.reference_files.map(({preview_data_url,...ref})=>ref)},null,2)}</pre></details>
        </div>
      </DataComponent>}
    </div>
    {visible("audit-method")&&<ReportSection id="audit-method" title="How to use this audit" queryId="summary" queryIds={["summary","artifacts"]} sourceRowsByQuery={{summary:summaryRows,artifacts:rows}} showHeading={false}>
      <RichNarrative id="audit:method" value={`## How to use this audit\n\nTreat the scores as a review queue. Inspect the prompt, candidate and original-image previews before deciding that a story misses the request. Check the rubric on a small set you label before using it for unattended restarts. Your selected **3/4 score and 0.80 confidence thresholds remain unchanged**.\n\nThis batch reused the production rubric and pure assessor with \`restarts=0\`. Full saved requests, including later directions, were compared independently with each current outline/plan or prose file. Originals were supplied at original detail. A temporary adapter handled the 34 historical numbered packages without changing the prompt sent to the API.\n\nThe batch continued through uncertain results to produce one review report. It did not restart stories or write checkpoint ledgers. The API answers provide distributions, not an explanatory critique. Historical outlines may predate later prompt revisions; score differences do not establish regression. No independent close reading or accuracy calibration of the entire corpus was performed.\n\n**Integrity:** ${s.source_changes} source files changed between snapshot and completion. **Recorded API usage:** ${s.input_tokens.toLocaleString()} input tokens, including ${s.cached_tokens.toLocaleString()} cached tokens; ${s.api_attempts} attempts. No billed monetary amount was inferred.\n\nCaptured ${snapshot.audit.capturedAt}. Source commit: \`${snapshot.audit.sourceRevision}\`. This is a fixed snapshot; new test stories and edits are not automatically rescored.`}/>
    </ReportSection>}
  </article>;
}
