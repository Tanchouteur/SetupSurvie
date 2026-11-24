"""Real Tk event-loop smoke; no services or private data."""
import os
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from transfer_wizard import Wizard

with tempfile.TemporaryDirectory() as name:
    wizard=Wizard(Path(name))
    wizard.root.update()
    assert wizard.root.title()=='Transférer SetupSurvie'
    assert len(wizard.actions)==(8 if os.name=='nt' else 7)
    wizard.launch(lambda:wizard.events.put(('text','fixture completed')))
    import time
    end=time.monotonic()+5
    while wizard.busy and time.monotonic()<end:
        wizard.root.update();time.sleep(.02)
    assert not wizard.busy
    assert 'fixture completed' in wizard.log.get('1.0','end')
    wizard.close()
print('Tk: real window, transfer actions, background worker and completion passed')
