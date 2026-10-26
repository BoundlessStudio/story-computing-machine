import React from "react";
import {DataComponent,DataTable,ReportSection,RichNarrative,useDataApp} from "../../data-app-public.jsx";
const pct=v=>v==null?"—":`${Math.round(v*100)}%`;
const yesno=v=>v==null?"—":v?"Yes":"No";
const columns=[{field:"title",label:"Story"},{field:"attempt_label",label:"Outline"},{field:"honors_request",label:"Honors?",renderCell:yesno},{field:"confidence",label:"Confidence",renderCell:pct},{field:"probability_yes",label:"P(Yes)",renderCell:pct},{field:"action",label:"Action"}];
export function CheckpointTrialSummary(){
 const {snapshot,visible}=useDataApp();
 if(!snapshot.queries.checkpoint_trials||!visible("checkpoint-trials-summary"))return null;
 const rows=snapshot.queries.checkpoint_trials.rows;
 const summary=snapshot.queries.checkpoint_trial_summary.rows;
 const s=summary[0];
 return <section aria-label="Live outline checkpoint observations">
  <ReportSection id="checkpoint-trials-summary" title="Outline checkpoint behavior" queryId="checkpoint_trial_summary" sourceRows={summary} showHeading={false}>
   <RichNarrative id="checkpoint-trials:summary" value={`## Three uncertain outline results halted for user judgment\n\nFive real outline calls allowed **${s.would_proceed} to proceed** and referred **${s.asked_user} uncertain results** to the user. No automatic restart was triggered and no final-story gate ran. One fresh start was explicitly user-directed. These are observations of the checkpoint policy, not proof of literary quality or measured classification accuracy.`}/>
  </ReportSection>
  <DataComponent id="checkpoint-trials-table" title="Five live outline decisions" queryId="checkpoint_trials" kind="table" sourceRows={rows} displayRows={rows} description="Native confidence is distinct from P(Yes). The gate requires at least 0.80 confidence; all native answers, probabilities and usage are preserved in the source records.">
   <DataTable rows={rows} columns={columns} searchable={false} compactNumbers={false} label="Five live outline decisions"/>
  </DataComponent>
  <ReportSection id="checkpoint-trials-scope" title="Scope of the trial" queryId="checkpoint_trials" sourceRows={rows} showHeading={false}>
   <RichNarrative id="checkpoint-trials:scope" value="The sky request was clarified before its final outline trial: outside others must provide the bridge making magic possible in a magicless world. That change of input limits comparisons across the three attempts. Candidate rewrites and their package changes are excluded from this merge; they remain on a separate local branch. No completed replacement prose is claimed. The corpus audit below is a fixed earlier snapshot, with its complete source evidence and all prior evaluation versions retained."/>
  </ReportSection>
 </section>;
}
