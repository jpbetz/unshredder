import Image
import itertools
import inspect
import copy
import math
import pprint

class ShreddedImage:
  def __init__(self, image, shredcount, shredwidth):
    self.image = image
    self.width = image.size[0]
    self.height = image.size[1]
    self.pixelMap = image.load()
    self.shredcount = shredcount
    self.shredwidth = shredwidth
  
  def show(self):
    self.image.show()

class Shred:
  def __init__(self, left, top, right, bottom):
    self.left = left
    self.top = top
    self.right = right
    self.bottom = bottom
    
  def __str__(self):
    return "%s-%s" % (self.left, self.right)
    
  def asTuple(self):
    return (self.left, self.top, self.right, self.bottom)

class ShredGroup:
  def __init__(self, shreds):
    self.shreds = shreds

  def __str__(self):
    return str(map(lambda x: str(x), self.shreds))
    
  def add(self, shredGroup):
    self.shreds.extend(shredGroup.shreds)

class MetaShreds:
  def __str__(self):
    return str(map(lambda x: str(x), self.metashreds))
  
  @staticmethod
  def createFromImage(shreddedImage):
    metashreds = []
    for i in range(0, shreddedImage.shredcount):
      shred = Shred(shreddedImage.shredwidth*i, 0, shreddedImage.shredwidth*(i+1), shreddedImage.height)
      metashreds.append(ShredGroup([shred]))
    return MetaShreds(shreddedImage, metashreds)

  def __init__(self, shreddedImage, metashreds):
    self.shreddedImage = shreddedImage
    self.metashreds = metashreds
    self.lCache = {}
    self.rCache = {}
    self.scoreCache = {}

  def show(self):
    self.shreddedImage.show()
       
  def findAdjacentShreds(self):
    shredcount = len(self.metashreds)
    while len(self.metashreds) > 1:
      lowestScore = float('inf')
      nextLowestScore = float('inf')
      for leftShred, rightShred in itertools.permutations(self.metashreds, 2):
        leftIdx = self.metashreds.index(leftShred)
        rightIdx = self.metashreds.index(rightShred)
        s = self.score(leftShred, rightShred)
        print "score for option (%s,%s) is %s" % (leftIdx, rightIdx, s)
        if s < lowestScore:
          nextLowestScore = lowestScore
          lowestScore = s
          lowestScoreLeftShred = leftShred
          lowestScoreRightShred = rightShred
          lowestScoreLeftShredIdx = leftIdx
          lowestScoreRightShredIdx = rightIdx
          
      if abs(lowestScore - nextLowestScore)/float(nextLowestScore) < 0.1:
        print "close call!  lowestScore : %s, nextLowestScore: %s" % (lowestScore, nextLowestScore)
        
      if len(self.metashreds) == -1: # disabled
        self.combine(lowestScoreRightShredIdx, lowestScoreLeftShredIdx)
      else:
        self.combine(lowestScoreLeftShredIdx, lowestScoreRightShredIdx)
      
  def combine(self, leftShredIdx, rightShredIdx):
    leftShredGroup = self.metashreds[leftShredIdx]
    rightShredGroup = self.metashreds[rightShredIdx]
    leftShredGroup.shreds.extend(rightShredGroup.shreds)
    combined = ShredGroup(leftShredGroup.shreds)
    self.metashreds[leftShredIdx] = combined
    self.metashreds.pop(rightShredIdx)
    print "combining left: ", leftShredIdx, " right: ", rightShredIdx, "combined:", self
    
  def getRightPixels(self, shredGroup):
    rightmostShred = shredGroup.shreds[-1]
    if rightmostShred not in self.rCache:
      rightmostColumn = rightmostShred.right-1
      pixels = []
      for i in range(0, rightmostShred.bottom):
        pixels.append(self.shreddedImage.pixelMap[rightmostColumn, i])
      self.rCache[rightmostShred] = pixels
    else:
      pixels = self.rCache[rightmostShred]
    return pixels
    
  def getLeftPixels(self, shredGroup):
    leftmostShred = shredGroup.shreds[0]
    if shredGroup not in self.lCache:
      leftmostColumn = leftmostShred.left
      pixels = []
      for i in range(0, leftmostShred.bottom):
        pixels.append(self.shreddedImage.pixelMap[leftmostColumn, i])
      self.lCache[leftmostShred] = pixels
    else:
      pixels = self.lCache[leftmostShred]
    return pixels

  def score(self, leftShred, rightShred):
    return self.score_full(leftShred, rightShred)
    #return self.score_top(leftShred, rightShred)
    
  def score_top(self, leftShred, rightShred):
    left = self.getRightPixels(leftShred)
    right = self.getLeftPixels(rightShred)
    score = 0
    for c in range(0, 2):
      score += abs(left[0][c] - right[0][c])
    return score
    
  def score_full(self, leftShred, rightShred):
    key = (leftShred, rightShred) 
    if key not in self.scoreCache:
      left = self.getRightPixels(leftShred)
      right = self.getLeftPixels(rightShred)
      score = 0
      for l, r in zip(left, right):
        for c in range(0, 2):
          score += abs(l[c] - r[c])
      self.scoreCache[key] = score
    else:
      score = self.scoreCache[key]
    return score
  
  def findBestPermutation(self):
    permutationCount = math.factorial(len(self.metashreds))
    print "permuation count: ", permutationCount
    permutations = itertools.permutations(self.metashreds)
    lowestScore = float('inf')
    lowestScorePermutation = None
    x = 0
    for permutation in permutations:
      x += 1
      score = self.scorePermutation(permutation)
      if score < lowestScore:
        lowestScore = score
        lowestScorePermutation = permutation
        print "------------------- found lower score varient: ", lowestScore
      pctDone = x*100.0/permutationCount
      ratioDone = x/permutationCount
      if ratioDone % 100 == 0: print "%.2f pct. done (" % pctDone ,x,"/",permutationCount,")"
    return MetaShreds(self.shreddedImage, lowestScorePermutation)

  def scorePermutation(self, permutation):
    diff = 0
    for i in range(0, len(permutation)-1):
      diff += self.score(permutation[i], permutation[i+1])
    return diff

def flatten(listOfLists):
    "Flatten one level of nesting"
    return list(itertools.chain.from_iterable(listOfLists))

def stitchTogether(im, originalMetashreds, orderedMetashreds):
  out = Image.new(im.mode, im.size)
  shreds = flatten(map(lambda shredGroup: shredGroup.shreds, originalMetashreds.metashreds))
  orderedshreds = flatten(map(lambda shredGroup: shredGroup.shreds, orderedMetashreds.metashreds))
  
  
  print "shreds: ", str(map(lambda x: str(x), shreds))
  print "ordered shreds: ", str(map(lambda x: str(x), orderedshreds))
  
  l = orderedshreds[:6]
  r = orderedshreds[6:]
  orderedshreds = r + l
  
  print "ordered shreds resorted: ", str(map(lambda x: str(x), orderedshreds))
  
  for i in range(0, len(shreds)):
    shred = shreds[i]
    orderedshred = orderedshreds[i]
    region = im.crop(orderedshred.asTuple())
    out.paste(region, shred.asTuple())
  return out

#MetaShreds.getLeftPixels = Memoize(MetaShreds.getLeftPixels)
#MetaShreds.getRightPixels = Memoize(MetaShreds.getRightPixels)

shredcount = 20 # 3,6,10,15..20

# load source image
im = Image.open("shredded%s.png" % shredcount)
#im = Image.open("shredded.png")

shredwidth = 25 # width/shredcount

# find the shreads

shreddedImage = ShreddedImage(im, shredcount, shredwidth)
original = MetaShreds.createFromImage(shreddedImage)
varient = MetaShreds.createFromImage(shreddedImage)

varient.findAdjacentShreds()
print "remaining permutable shred groups: ",len(varient.metashreds)
#varient = varient.findBestPermutation()

print varient
#original.show()
stitchTogether(im, original, varient).show()
