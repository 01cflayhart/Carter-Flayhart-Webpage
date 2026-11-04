"""Export a server-free personal site with independent ATP/WTA data files."""
import argparse
from pathlib import Path
import shutil

from .engine import SURFACES, parse_date, statistics
from .server import Application
from .update import ROOT, atomic_json


def export(root=ROOT, output=None):
    root=Path(root);out=Path(output) if output else root/'_site'
    # Copy only public website assets. Never publish the project/data directory.
    shutil.copytree(root/'site',out,dirs_exist_ok=True)
    tennis=out/'sports'/'tennis'
    shutil.copytree(root/'web',tennis,dirs_exist_ok=True)
    (out/'.nojekyll').touch()
    (tennis/'runtime.js').write_text('window.COURT_STATIC = true;\n')
    for tour in ('ATP','WTA'):
        app=Application(root,'data/current/'+tour)
        snapshot,players=app.load()
        if snapshot.get('tour')!=tour or any(not p.startswith('valuebetennis:'+tour+':') for p in players):
            raise ValueError('Tour namespace validation failed')
        dest=tennis/'data'/tour
        atomic_json(dest/'meta.json',app.api('/api/meta',{}))
        for p in players.values():
            atomic_json(dest/'players'/(p['id'].replace(':','_')+'.json'),p)
        for surface in ('Overall',*SURFACES):
            for no_ret in (False,True):
                rows=[]
                for p in players.values():
                    row={k:v for k,v in p.items() if k not in ('history','stats')}
                    row['selected_rank']=p['rank'] if surface=='Overall' else p['surfaces'][surface]['rank']
                    row['selected_rating']=p['rating'] if surface=='Overall' else p['surfaces'][surface]['rating']
                    row['form']=[r['won'] for r in p['history'][:5]][::-1]
                    row['stats']={basis:{period:statistics(p['history'],parse_date(snapshot['recent_start_exclusive'] if period=='recent' else snapshot['window_start_exclusive']),basis,no_ret,surface) for period in ('year','recent')} for basis in ('atp','power')}
                    rows.append(row)
                atomic_json(dest/'rankings'/(surface+'-'+str(int(no_ret))+'.json'),rows)
        print(tour+': exported '+str(len(players))+' separate notebooks',flush=True)
    print('Public artifact: '+str(out),flush=True)
    return out


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output')
    args=parser.parse_args();export(output=args.output)
