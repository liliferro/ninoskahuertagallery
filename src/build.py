import base64,os
D='/tmp/claude-0/-home-claude/5ddf1c52-7e53-5ddd-a594-4f4b72cebef9/scratchpad'
b=lambda p: base64.b64encode(open(p,'rb').read()).decode()
F=D+'/nh/project/fonts/'
L='/mnt/user-data/outputs/brand-book-ninoska-huerta/assets/'
hero=open(D+'/hero/src.html').read()
core=hero[hero.index('  // Complementary pairs'):hero.index('  // ---------- loop')]
app=open('app.js').read().replace('{{KINETIC_CORE}}',core)
s=open('page.html').read()
s=s.replace(' Each piece is shipped with its documentation.','')
s=s.replace('Exhibitions, studio visits and conversations with our artists on the gallery’s channel.','Videos from the gallery on our YouTube channel.')
s=s.replace('{{DATA}}',open('../content/content.js').read()+'\n'+open('data.js').read()).replace('{{APP}}',app)
s=s.replace('{{JOST}}',b(F+'Jost-wght.woff2')).replace('{{NEWS}}',b(F+'Newsreader-wght.woff2')).replace('{{NEWSI}}',b(F+'Newsreader-wght-italic.woff2')).replace('{{MONO}}',b(F+'IBMPlexMono-400.woff2'))
s=s.replace('{{LOGO}}','data:image/svg+xml;base64,'+b(L+'nh-logo-horizontal.svg')).replace('{{LOGO_R}}','data:image/svg+xml;base64,'+b(L+'nh-logo-horizontal-reversed.svg'))
assert '{{' not in s
open('artifact.html','w').write(s)
head,rest=s.split('</style>',1)
fav='data:image/svg+xml;base64,'+b(L+'nh-logo-short.svg')
full=('<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
 '<meta name="description" content="Ninoska Huerta Gallery, Coral Gables, Miami. Constructivism, abstraction and kinetic art: Latin American masters and new voices. By appointment only.">\n'
 f'<link rel="icon" href="{fav}">\n'+head+'</style>\n</head>\n<body>\n'+rest+'\n</body>\n</html>\n')
os.makedirs('/mnt/user-data/outputs/web-ninoska-huerta',exist_ok=True)
open('/mnt/user-data/outputs/web-ninoska-huerta/index.html','w').write(full)
print(len(full)//1024,'KB')
