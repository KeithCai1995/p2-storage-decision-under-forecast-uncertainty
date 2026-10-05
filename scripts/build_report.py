"""Build the P2 PDF from the corrected current CSVs and baseline figures."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from xml.sax.saxutils import escape
import pandas as pd
import reportlab
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Spacer,PageBreak,Image,KeepTogether
ROOT=Path(__file__).resolve().parents[1]
VERSION='1.0.1'
LABELS={'seasonal_naive':'Seasonal naive','median_risk_neutral':'Median risk neutral','raw_cvar':'Raw CVaR','static_cvar':'Static CVaR','adaptive_risk_neutral':'Adaptive risk neutral','adaptive_cvar':'Adaptive CVaR','oracle':'Oracle'}

def build(destination:Path):
    fonts=Path(reportlab.__file__).parent/'fonts'
    for suffix,name in [('', 'Vera.ttf'),('-Bold','VeraBd.ttf'),('-Italic','VeraIt.ttf'),('-BoldItalic','VeraBI.ttf')]:
        pdfmetrics.registerFont(TTFont('PortfolioSans'+suffix,str(fonts/name)))
    pdfmetrics.registerFontFamily('PortfolioSans',normal='PortfolioSans',bold='PortfolioSans-Bold',italic='PortfolioSans-Italic',boldItalic='PortfolioSans-BoldItalic')
    source=json.loads((ROOT/'report/report_text.json').read_text(encoding='utf-8'))
    metrics={name:pd.read_csv(ROOT/'experiments'/name/'strategy_metrics.csv').set_index('strategy') for name in ['baseline','cvar_weight_070','cvar_weight_085']}
    for name in metrics:
        manifest=json.loads((ROOT/'experiments'/name/'run_manifest.json').read_text())
        if manifest.get('cvar_estimator')!='empirical_fixed_probability_mass_v1':raise ValueError('Regenerate fixed-mass reference snapshot: '+name)
    base=metrics['baseline'];frontier=pd.read_csv(ROOT/'experiments/baseline/risk_frontier.csv').set_index('cvar_weight')
    styles={
        'body':ParagraphStyle('body',fontName='PortfolioSans',fontSize=9.8,leading=13.2,spaceAfter=8),
        'head':ParagraphStyle('head',fontName='PortfolioSans-Bold',fontSize=13,leading=16,spaceBefore=6,spaceAfter=9,keepWithNext=True),
        'sub':ParagraphStyle('sub',fontName='PortfolioSans-Bold',fontSize=10.6,leading=14,spaceBefore=5,spaceAfter=6,keepWithNext=True),
        'title':ParagraphStyle('title',fontName='PortfolioSans-Bold',fontSize=23,leading=27,spaceAfter=12),
        'kicker':ParagraphStyle('kicker',fontName='PortfolioSans-Bold',fontSize=8.5,leading=11,spaceAfter=10,textColor=colors.HexColor('#565656')),
        'subtitle':ParagraphStyle('subtitle',fontName='PortfolioSans',fontSize=12,leading=16,spaceAfter=14),
        'cap':ParagraphStyle('cap',fontName='PortfolioSans',fontSize=8.5,leading=11,spaceBefore=4,spaceAfter=10,textColor=colors.HexColor('#444444')),
        'cell':ParagraphStyle('cell',fontName='PortfolioSans',fontSize=8.3,leading=11),
        'cellhead':ParagraphStyle('cellhead',fontName='PortfolioSans-Bold',fontSize=8.3,leading=11),
        'num':ParagraphStyle('num',fontName='PortfolioSans',fontSize=8.3,leading=11,alignment=2),
        'ref':ParagraphStyle('ref',fontName='PortfolioSans',fontSize=8.2,leading=10.4,spaceAfter=4.8),
    };story=[]
    def p(text,style='body'):story.append(Paragraph(text,styles[style]))
    def old(index,style='body'):p(escape(source['paragraphs'][str(index)]),style)
    def h(text):p(text,'head')
    def sub(text):p(text,'sub')
    def page():story.append(PageBreak())
    def n(strategy,col):return f'{base.loc[strategy,col]:.2f}'
    def table(rows,widths,numeric=False):
        cells=[[Paragraph(escape(str(x)),styles['cellhead' if i==0 else 'num' if numeric and j>0 else 'cell']) for j,x in enumerate(row)] for i,row in enumerate(rows)]
        t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#ededed')),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#999999')),('LINEBELOW',(0,-1),(-1,-1),.5,colors.HexColor('#aaaaaa')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8f8f8')])]))
        story.extend([t,Spacer(1,10)])
    def fig(index,width,caption):
        names=['representative_schedule','cumulative_profit','profit_distribution','decision_regret','risk_frontier','battery_sensitivity']
        im=Image(str(ROOT/'outputs/figures'/f'figure_{index}_{names[index-1]}.png'))
        ratio=im.imageHeight/im.imageWidth
        im.drawWidth=width;im.drawHeight=width*ratio;im.hAlign='CENTER'
        story.append(KeepTogether([im,Paragraph(f'Figure {index}. {caption} Source: regenerated v1.0.1 baseline.',styles['cap'])]))
    p('DOCTORAL APPLICATION TECHNICAL PORTFOLIO','kicker')
    p('From Calibrated Forecasts<br/>to Risk-constrained<br/>Storage Decisions','title')
    p('A reproducible mean-CVaR benchmark for day-ahead battery scheduling','subtitle')
    p('Haorui Cai | Revised 4 October 2026 | Code v1.0.1','kicker')
    p('<b>SIMULATED BENCHMARK - NOT A TRADING SYSTEM.</b> All prices, profits, losses and regret values are simulated. They are not employer evidence or realised market revenue.')
    sub('Abstract')
    p('Project 1 showed that a forecast interval can look better statistically after calibration. This project asks whether that change leads to a better battery decision. It uses the 83-day simulated evaluation block from Project 1 and a linear battery model with state of charge (SOC), efficiency, power limits and required end-of-day SOC. Seven schedules are compared, including risk-neutral and CVaR versions. Adaptive-CVaR earns '+n('adaptive_cvar','mean_daily_profit_eur')+' simulated EUR/day, compared with '+n('raw_cvar','mean_daily_profit_eur')+' for raw-CVaR and '+n('static_cvar','mean_daily_profit_eur')+' for static-CVaR. Its empirical 90%-CVaR loss is '+n('adaptive_cvar','empirical_cvar_loss_eur')+' EUR, with no violations of the simplified constraints. A wider interval is not automatically a better input for a decision. This revision uses fixed-probability-mass CVaR and synchronises the report with corrected outputs.')
    h('1. Motivation and contribution');old(9)
    p('Two choices keep the comparison inspectable. First, the linear battery model restores terminal SOC to initial SOC, preventing profit from borrowing end-of-day energy value. Second, raw, static and adaptive forecast paths use the same battery and scoring rules. The contribution is an auditable link from forecast uncertainty to constrained decisions, not a new CVaR or bidding formulation.')
    page();h('2. Decision model');sub('2.1 Battery physics');old(15)
    p('SOC<sub>t+1</sub> = SOC<sub>t</sub> + 0.94 charge<sub>t</sub> - discharge<sub>t</sub> / 0.94, with 0 &lt;= SOC &lt;= 2 and 0 &lt;= charge, discharge &lt;= 1.')
    sub('2.2 Scenario profit, optimisation and CVaR reporting')
    p('Profit is discharge revenue minus charging and throughput costs. The risk-neutral objective maximises average scenario profit; the risk-aware objective subtracts weight times loss CVaR, with alpha 0.90 and base weight 0.55. The Rockafellar-Uryasev auxiliary-variable formulation is solved with SciPy/HiGHS: CVaR = min over zeta of zeta + sum(u<sub>s</sub>)/((1 - alpha) N), with u<sub>s</sub> &gt;= loss<sub>s</sub> - zeta and u<sub>s</sub> &gt;= 0.')
    p('<b>Reporting definition in v1.0.1.</b> Sort losses from largest to smallest. Let m = (1 - alpha) n, k = floor(m) and r = m - k. CVaR is (sum of the k largest losses + r times the next loss)/m; omit the next loss when r is zero. Thus 60 equally weighted scenarios contribute six observations and 83 evaluation days contribute 8.3 observations. This preserves fixed tail probability mass with ties and fractional boundaries (Rockafellar and Uryasev, 2002). The LP optimisation formula is unchanged.')
    sub('2.3 Feasibility and assumptions')
    p('All seven strategies over 83 days have zero reported constraint violations and zero simultaneous charge/discharge throughput. Tests independently recompute SOC transitions and terminal SOC. These checks apply to the simplified benchmark constraints.')
    table(source['assumptions'],[120,166,214])
    sub('2.4 Relationship to existing work')
    p('CVaR optimisation is established (Rockafellar and Uryasev, 2000, 2002). Donti et al. (2017) and Elmachtoub and Grigas (2022) connect prediction and decision loss. Kim et al. (2021) and Toubeau et al. (2021) study uncertain storage scheduling; Yeh et al. (2025) and Alghumayjan et al. (2025) connect conformal uncertainty to decisions. This portfolio integrates those ideas with profit, regret, tail risk and feasibility checks.')
    page();h('3. Forecast-to-scenario and experimental design')
    p('Project 1 supplies seven marginal quantiles per hour. Interpolation produces 60 possible 24-hour paths. A shared Gaussian factor has loading 0.65, giving distinct latent hours Pearson correlation 0.4225 and Gaussian-copula Spearman correlation about 0.41 before clipping and interpolation. This exchangeable toy assumption is not a neighbouring-hour or lag-specific correlation model. Static and adaptive paths are rescaled around the median so their q10-q90 spread matches the calibrated interval. That bridge does not establish joint calibration of complete 24-hour paths.')
    table(source['strategies'],[147,203,150])
    fig(1,410,'Representative adaptive-CVaR schedule, showing power and SOC feasibility and restoration of terminal SOC.')
    p('The chosen schedule uses forecast information; realised prices are used to score it. The oracle is a deliberately infeasible information benchmark. Operational issuance-time limitations are stated in Section 7.')
    page();h('4. Main results')
    p('All financial values below are simulated EUR. The main comparison uses 83 evaluation days at CVaR weight 0.55. CVaR uses the worst 10% loss probability mass. Mean profit and regret are per day.')
    rows=[['Strategy','Mean profit','5th pct profit','CVaR loss','Mean regret']]
    for s in LABELS:rows.append([LABELS[s]]+[n(s,c) for c in ['mean_daily_profit_eur','fifth_percentile_profit_eur','empirical_cvar_loss_eur','mean_regret_eur']])
    table(rows,[152,87,87,87,87],True)
    p('The seasonal rule loses '+f"{abs(base.loc['seasonal_naive','mean_daily_profit_eur']):.2f}"+' EUR/day. The median forecast produces positive mean profit. Raw-CVaR earns '+n('raw_cvar','mean_daily_profit_eur')+' with CVaR loss '+n('raw_cvar','empirical_cvar_loss_eur')+'. Static-CVaR lowers tail loss to '+n('static_cvar','empirical_cvar_loss_eur')+' but earns '+n('static_cvar','mean_daily_profit_eur')+'. Adaptive-CVaR combines '+n('adaptive_cvar','mean_daily_profit_eur')+' mean profit with CVaR loss '+n('adaptive_cvar','empirical_cvar_loss_eur')+', the lowest tail loss among non-oracle strategies in this base comparison.')
    fig(2,500,'Cumulative simulated profit over the evaluation block; profit is unchanged by the reporting correction.')
    p('The oracle earns '+n('oracle','mean_daily_profit_eur')+' EUR/day, leaving substantial regret for forecast-based strategies. It requires future realised prices and is not a realistic trading opportunity. Negative loss CVaR means even its selected worst tail remains profitable in this simulation.')
    page();h('5. Tail risk and regret')
    fig(3,435,'Simulated daily profit distributions for feasible benchmark strategies.')
    fig(4,415,'Mean daily regret relative to the perfect-foresight oracle; lower is better.')
    sub('5.1 What calibration changed')
    p('Static calibrated paths reduce tail losses but give up some profit relative to raw-CVaR. Adaptive-CVaR gives a more favourable balance in this base simulation. Coverage alone is not a decision metric: calibration changes path dispersion, which changes dispatch under efficiency, throughput cost and SOC constraints. These results do not establish the same ranking in another market or seed.')
    page();sub('5.2 CVaR-weight sensitivity')
    p('Alongside the supplied 0.55 and 0.85 settings, I ran a pre-planned 0.70 test on the same simulated benchmark and seed on 2 October. This table uses the corrected reporting definition; original run records retain their earlier diagnostic values.')
    rows=[['Weight','Adaptive mean profit','5th pct profit','CVaR loss','Throughput MWh/day']]
    for w,name in [(0.55,'baseline'),(0.70,'cvar_weight_070'),(0.85,'cvar_weight_085')]:
        r=metrics[name].loc['adaptive_cvar'];rows.append([f'{w:.2f}']+[f'{r[c]:.2f}' for c in ['mean_daily_profit_eur','fifth_percentile_profit_eur','empirical_cvar_loss_eur','mean_throughput_mwh']])
    table(rows,[53,121,104,104,118],True)
    p('Tail loss and fifth-percentile profit improve across these adaptive-CVaR runs while throughput decreases. Mean profit is non-monotonic. Weight 0.70 reduces tail risk relative to 0.55 with slightly less profit. This single-seed comparison does not establish an optimum; the base remains 0.55.')
    h('6. Risk preference and battery parameters')
    fig(5,385,'Mean simulated profit versus fixed-mass empirical CVaR loss, using a separate frontier scenario sample.')
    p(f"In the frontier sample, increasing the weight from 0 to 0.85 reduces CVaR loss from {frontier.loc[0.,'empirical_cvar_loss_eur']:.2f} to {frontier.loc[0.85,'empirical_cvar_loss_eur']:.2f} EUR. Mean profit at 0.85 is {frontier.loc[0.85,'mean_daily_profit_eur']:.2f}, compared with {frontier.loc[0.55,'mean_daily_profit_eur']:.2f} at 0.55. These values differ from the main sensitivity runs because the frontier draws its own scenario sample. Non-monotone profit reflects finite scenarios and one realised evaluation path.")
    page();fig(6,445,'A 28-day diagnostic of median-forecast profit across energy capacity and efficiency.');old(52)
    h('7. What the project still cannot answer');sub('7.1 Limitations and timing boundary');old(55)
    p('<b>Issuance-time boundary.</b> In the supplied CSV, issue_time equals target_time for horizon 1. A separate prior-day market gate-closure timestamp is not recorded. This 24-hour scheduling benchmark therefore does not itself verify operational day-ahead forecast availability. A real-data study would need publication-time checks before any bidding claim.')
    old(59)
    page();sub('7.2 Reproducibility and revision record')
    p('The manifest records seed 20260817, 83 days, 60 scenarios per day, battery settings, software and the estimator identifier. Current snapshots are in experiments/baseline, experiments/cvar_weight_070 and experiments/cvar_weight_085. The baseline figures in this report are regenerated from corrected code.')
    p('python -m unittest discover -s tests -v<br/>python scripts/verify_release.py')
    p('<b>Assisted verification on 4 October 2026:</b> Linux, Python 3.12.14, NumPy 2.3.5, pandas 2.2.3 and SciPy 1.17.0; 11 unit tests and 9/9 rerun comparisons passed at absolute tolerance 1e-10. Across 3,744 paired old/new diagnostic solves, schedules, expected profit and LP objectives were identical. The earlier Windows/Python 3.13.15 personal logs remain in evidence/personal_run/2026-10-02. New evidence is in evidence/assisted_review/2026-10-04_cvar_fix. At this assisted review, corrected Windows runs and cross-platform CI had not yet been executed.')
    sub('7.3 Doctoral extension');old(61)
    sub('References')
    references=[source['paragraphs'][str(i)] for i in range(63,74)]
    references.insert(1,'Rockafellar, R.T. and Uryasev, S. (2002). Conditional value-at-risk for general loss distributions. Journal of Banking & Finance 26, 1443-1471. https://sites.math.washington.edu/~rtr/papers/rtr187-CVaR2.pdf')
    for i,s in enumerate(references,1):
        at=s.find('http')
        body=s[:at].strip() if at>=0 else s;url=s[at:].strip() if at>=0 else ''
        p(f'{i}. '+escape(body)+(f' <link href="{escape(url)}" color="#345577">Source</link>.' if url else ''),'ref')
    def decorate(canvas,doc):
        canvas.saveState();canvas.setFont('PortfolioSans',7.5);canvas.setFillColor(colors.HexColor('#666666'))
        canvas.drawString(56,767,'P2 | SIMULATED BENCHMARK | Haorui Cai');canvas.drawRightString(556,767,'v1.0.1')
        canvas.drawString(56,29,'Revised 4 October 2026');canvas.drawRightString(556,29,str(doc.page));canvas.restoreState()
    destination.parent.mkdir(parents=True,exist_ok=True)
    doc=SimpleDocTemplate(str(destination),pagesize=letter,leftMargin=56,rightMargin=56,topMargin=49,bottomMargin=45,title='From Calibrated Forecasts to Risk-constrained Storage Decisions',author='Haorui Cai',subject='P2 CVaR reporting correction v1.0.1')
    doc.build(story,onFirstPage=decorate,onLaterPages=decorate)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'report/P2_Mini_Paper_Haorui_Cai.pdf');args=parser.parse_args();build(args.output);print('Report generated:',args.output.name)
if __name__=='__main__':main()
