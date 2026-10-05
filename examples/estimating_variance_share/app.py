"""Shiny companion to Supplementary File 3. Run with the root run_shiny.sh.

Every analysis uses model.py, the same module used by run_case.py and tests.
Long bootstrap jobs run outside Shiny's reactive graph. A generation identifier
prevents a result from an older dataset appearing beside a newer simulation.
"""
from pathlib import Path
from dataclasses import asdict
import asyncio,io,json,zipfile
import numpy as np
import pandas as pd
from shiny import App,reactive,render,ui,req
from model import Settings,simulate,analyse,bootstrap,truth
from plots import relationship_plot,components_plot,diagnostics_plot
ROOT=Path(__file__).resolve().parent
CSS='''body{color:#20303d;background:#fafbf9}.container-fluid{max-width:1450px;margin:auto}
h1,h2,h3{font-weight:600}.note{border-left:3px solid #2166ac;padding:12px 16px;background:#f0f5f8;margin:16px 0}
.small-note{font-size:.88rem;color:#52606b}.nav-tabs{margin-top:12px;margin-bottom:20px}
.tab-content{padding:8px 12px}.bslib-sidebar-layout>.sidebar{background:#f1f3ef}
.form-group{margin-bottom:12px}.table{font-variant-numeric:tabular-nums}a{color:#2166ac}'''
app_ui=ui.page_sidebar(
 ui.sidebar(
  ui.h3('Simulation'),
  ui.p('Change a setting, then generate the data. The seed makes each case reproducible.',class_='small-note'),
  ui.input_numeric('n','Distinct genotypes',800,min=100,max=5000,step=100),
  ui.input_numeric('repeats','Height measurements per genotype',3,min=2,max=10),
  ui.input_slider('G','Breeding-value variance (cm²)',min=.1,max=3,value=1,step=.1),
  ui.input_slider('E','Environmental variance per measurement (cm²)',min=.1,max=4,value=1,step=.1),
  ui.input_slider('b','Local log-fitness slope',min=-1.5,max=1.5,value=.7,step=.1),
  ui.input_slider('H','Local log-fitness curvature',min=-2,max=-.1,value=-.7,step=.1),
  ui.input_numeric('output_mean','Expected offspring at mean breeding value',4,min=.5,max=10,step=.5),
  ui.input_checkbox('stress','Add a fourth-order term to test the quadratic assumption',False),
  ui.input_numeric('seed','Simulation seed',20261005,min=0,max=4294967295,step=1),
  ui.input_action_button('generate','Generate and estimate',class_='btn-primary'),
  ui.hr(),ui.download_button('download_case','Download this case'),
  ui.a('Read Supplementary File 3',href='Supplementary_File_3_Worked_Estimation.pdf',target='_blank'),
  width=305),
 ui.tags.style(CSS),
 ui.p('A worked example for Additive Channels in Curved Fitness Landscapes',class_='small-note'),
 ui.h2('From reproductive counts to a variance share'),
 ui.p('Follow the five estimation steps using one trait and one reproductive episode.'),
 ui.div(ui.output_text('case_status'),class_='note'),
 ui.navset_tab(
  ui.nav_panel('1. Define the data',
   ui.h3('Height measurements and surviving offspring'),
   ui.p('Each genotype has an unobserved breeding value for height. Independent clonal replicates provide noisy height measurements. A separate reproductive assay records a count of surviving offspring, including zeros.'),
   ui.p('This teaching model assumes additive genetic effects, independent environments and unrelated genotypes. Clonal variation would not identify additive variance in a model with dominance, epistasis or shared permanent environments.'),
   ui.output_table('data_summary'),ui.output_data_frame('observations'),
   ui.p('The true breeding values are saved separately for checking the simulation. The estimator does not receive them.',class_='small-note')),
  ui.nav_panel('2. Fit the mean',
   ui.h3('Average output at each breeding value'),
   ui.p('First estimate genetic and environmental variation from the repeated height measurements. Then fit a Poisson model with a quadratic log mean, averaging its likelihood over each genotype’s uncertain breeding value. Zero offspring counts are valid observations; they are never logged.'),
   ui.output_plot('relationship',height='420px'),ui.output_text('calibration_text'),
   ui.p('The left curve predicts counts from the noisy measurements. The right curve estimates expected fitness at a specified breeding value. These are different conditional means.',class_='note')),
  ui.nav_panel('3–4. Calculate the share',
   ui.h3('Keep the absolute components beside their ratio'),
   ui.p('The fitted slope describes local proportional change in expected output; curvature describes how that slope changes. Combine them with breeding-value variance to obtain the two contributions to variation in log expected fitness.'),
   ui.output_table('estimates'),ui.output_plot('components',height='390px'),
   ui.p('A share of 0.7 means that the linear term contributes 70% of variance in the local quadratic description. It is not 70% of variation in observed offspring counts, and it does not establish response-to-selection accuracy.',class_='note'),
   ui.p('The naive comparison fits the predicted breeding values as exact and substitutes their smaller variance for genetic variance. Its error can change direction when slope and curvature are also re-estimated.',class_='small-note')),
  ui.nav_panel('5a. Quantify uncertainty',
   ui.h3('Repeat the entire estimation process'),
   ui.p('Each bootstrap sample generates new genetic values, height measurements and offspring counts from the fitted quadratic model. The analysis re-estimates both variance parameters and the fitness relationship.'),
   ui.input_numeric('B','Bootstrap replicates',200,min=20,max=1000,step=20),
   ui.input_task_button('run_bootstrap','Calculate intervals',label_busy='Calculating intervals…'),
   ui.output_text('bootstrap_status'),ui.output_table('intervals'),
   ui.p('The 95% percentile intervals are conditional on this observation and fitness model. Twenty replicates are only a quick demonstration. Use at least 500 for the worked result; model sensitivity is assessed separately in step 5.',class_='note')),
  ui.nav_panel('5b. Check the model',
   ui.h3('Compare predicted and observed output'),
   ui.output_plot('diagnostics',height='400px'),ui.output_text('model_check'),
   ui.p('The bars show approximate sampling variation of each observed bin mean under the fitted model, conditional on the estimated parameters. They are not simultaneous confidence bands. A good visual match does not prove the assumptions.'),
   ui.p('Try the fourth-order option. The primary fit remains quadratic. The additional curve fits cubic and quartic terms as a sensitivity analysis; its local quadratic share is not the R² of the complete fourth-order curve.'),
   ui.div(ui.output_text('truth_check'),class_='note'),
   ui.p('Further checks for real data include relatedness, unequal measurement precision, overdispersed counts, shared environments, non-Gaussian genetic values and whether a quadratic approximation is adequate. This example is not a replacement for an animal model or genomic mixed model.',class_='small-note')),
  id='steps'),title='Estimating the variance share',fillable=False)


def server(input,output,session):
    def make_case(s):
        d,A=simulate(s)
        return dict(settings=s,data=d,A=A,fit=analyse(d))
    case=reactive.value(make_case(Settings()))
    generation=reactive.value(0)
    intervals_value=reactive.value(None)
    error=reactive.value('')

    def requested():
        return Settings(n=int(input.n()),repeats=int(input.repeats()),G=input.G(),E=input.E(),
                        b=input.b(),H=input.H(),mean_output=input.output_mean(),
                        quartic=.08 if input.stress() else 0,seed=int(input.seed()))

    @ui.bind_task_button(button_id='run_bootstrap')
    @reactive.extended_task
    async def run_intervals(d,fit,B,seed,version):
        result=await asyncio.to_thread(bootstrap,d,fit,B,seed)
        return version,result

    @reactive.effect
    @reactive.event(input.generate)
    def regenerate():
        try:
            updated=make_case(requested())
        except (ValueError,TypeError) as exc:
            error.set(str(exc));return
        run_intervals.cancel()
        generation.set(generation.get()+1)
        intervals_value.set(None);case.set(updated);error.set('')

    @reactive.effect
    @reactive.event(input.run_bootstrap)
    def start_intervals():
        c=case.get()
        run_intervals(c['data'],c['fit'],int(input.B()),c['settings'].seed+1,generation.get())

    @reactive.effect
    def collect_intervals():
        version,value=run_intervals.result()
        if version==generation.get():intervals_value.set(value)

    @render.text
    def case_status():
        c=case.get();s=c['settings']
        try:pending=asdict(requested())!=asdict(s)
        except (TypeError,ValueError):pending=True
        text=f'Displayed case: {s.n} genotypes, {s.repeats} measurements each, seed {s.seed}. '
        text+='Fourth-order data; quadratic primary fit.' if s.quartic else 'Quadratic generating relationship.'
        if pending:text+=' Settings have changed: press Generate and estimate to apply them.'
        if error.get():text+=' Could not generate the requested case: '+error.get()
        return text

    @render.table
    def data_summary():
        c=case.get();d=c['data']
        return pd.DataFrame({'Measure':['Genotypes','Height measurements','Zero offspring counts','Mean offspring count'],
                             'Value':[len(d),len(d)*c['settings'].repeats,int((d.offspring==0).sum()),round(d.offspring.mean(),3)]})
    @render.data_frame
    def observations():return render.DataGrid(case.get()['data'].head(12).round(3),height='300px')
    @render.plot
    def relationship():
        c=case.get();return relationship_plot(c['data'],c['settings'],c['fit'])
    @render.text
    def calibration_text():
        e=case.get()['fit']['estimate']
        return f"Estimated breeding-value variance: {e['G']:.3f} cm². Environmental variance: {e['E']:.3f} cm². Reliability of the mean-height prediction: {e['reliability']:.3f}."
    @render.table
    def estimates():
        c=case.get();f=c['fit'];t=truth(c['settings'])
        names=['b','H','G','V_lin','V_quad','A_g']
        return pd.DataFrame({'Quantity':names,'Generating value':[t[k] for k in names],
                             'Latent-value estimate':[f['estimate'][k] for k in names],
                             'Naive estimate':[f['naive'][k] for k in names]}).round(4)
    @render.plot
    def components():
        c=case.get();return components_plot(c['settings'],c['fit'],intervals_value.get())
    @render.text
    def bootstrap_status():
        b=intervals_value.get()
        if b is None:return 'No intervals for the displayed dataset yet.'
        return f"Completed {len(b['draws'])} of {b['requested']} replicates; {len(b['failed'])} failed; {b['boundary_count']} fits reached a parameter boundary. Seed {b['seed']}."+(' Too many failures to report intervals.' if not b['intervals'] else '')
    @render.table
    def intervals():
        b=intervals_value.get();req(b is not None)
        return pd.DataFrame([{'Quantity':k,'Lower 2.5%':v[0],'Upper 97.5%':v[1]} for k,v in b['intervals'].items()]).round(4)
    @render.plot
    def diagnostics():return diagnostics_plot(case.get()['fit'])
    @render.text
    def model_check():
        f=case.get()['fit']
        text=f"Quartic minus quadratic AIC: {f['delta_aic']:.2f}; negative values favour the more flexible fit. The quartic fit's local quadratic share is {f['alternative_share']['A_g']:.3f}. AIC is a sensitivity comparison, not proof of model adequacy."
        if f['fit']['boundary']:text+=' The primary fit reached a parameter boundary: interpret intervals cautiously.'
        if f['alternative']['boundary']:text+=' The sensitivity fit reached a parameter boundary.'
        return text
    @render.text
    def truth_check():
        t=truth(case.get()['settings'])
        return f"Known only in this simulation: the local quadratic share is {t['A_g']:.3f}; the affine R² of the complete generating log mean is {t['full_log_mean_R2']:.3f}. They agree for the quadratic case and can differ when the fourth-order term is present."
    @render.download(filename='variance_share_case.zip',media_type='application/zip')
    def download_case():
        c=case.get();f=c['fit'];b=intervals_value.get();stream=io.BytesIO()
        summary=dict(settings=asdict(c['settings']),estimate=f['estimate'],truth=truth(c['settings']),
                     naive=f['naive'],alternative=f['alternative_share'],delta_aic=f['delta_aic'])
        if b:summary['bootstrap']={k:v for k,v in b.items() if k!='draws'}
        with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('observed_data.csv',c['data'].to_csv(index=False))
            z.writestr('simulation_truth.csv',pd.DataFrame({'id':c['data']['id'],'true_breeding_value':c['A']}).to_csv(index=False))
            z.writestr('results.json',json.dumps(summary,indent=2,allow_nan=False))
            if b:z.writestr('bootstrap_draws.csv',b['draws'].to_csv(index=False))
        yield stream.getvalue()

app=App(app_ui,server,static_assets={'/Supplementary_File_3_Worked_Estimation.pdf':ROOT/'Supplementary_File_3_Worked_Estimation.pdf'})
