import sys
from PIL import Image
d=sys.argv[1]; names=sys.argv[2:]
ims=[Image.open('%s/%s.png'%(d,n)).convert('RGB').resize((640,360)) for n in names]
rows=(len(ims)+1)//2
sheet=Image.new('RGB',(1280,360*rows),(255,255,255))
for i,im in enumerate(ims): sheet.paste(im,((i%2)*640,(i//2)*360))
sheet.save('%s/sheet.png'%d)
