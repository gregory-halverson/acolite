## def settings_read
## read ACOLITE settings from file to "settings" dict
## 
## Written by Quinten Vanhellemont 2017-11-30
## Last modifications: 2018-06-06 QV added None check for limit

def settings_read(file):
    settings={}
    with open(file, 'r') as f:
        for line in f.readlines():
            line = line.strip()
            if len(line) == 0: continue
            if line[0] in ['#',';']: continue
            split = line.split('=')
            var = split[0]
            val = split[1].split(',')
            if len(val) == 1:
                val = val[0]
                if val in ['True','true','1']: val=True
                if val in ['False','false','0']: val=False
                if val in ['None','none']: val=None
            if (var in ['limit']) & (val is not None): val = [float(i) for i in val]
            settings[var]=val
    return(settings)