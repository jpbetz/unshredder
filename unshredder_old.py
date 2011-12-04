import Image
import itertools
import inspect
import copy
import math
import random

def flatten(listOfLists):
    "Flatten one level of nesting"
    return list(itertools.chain.from_iterable(listOfLists))
  
def stitchTogether(im, metashreds, orderedmetashreds):
  # create a destination canvas
  out = Image.new(im.mode, im.size)
  
  shreds = flatten(metashreds)
  orderedshreds = flatten(orderedmetashreds)
  print "stitched together shreds: ", shreds
  print "stitched together orderedshreds", orderedshreds
  # cut a box and paste it to another region
  #box = (0,0, width/shredcount, height)
  #region = im.crop(box)
  #out.paste(region, (shredwidth,0, shredwidth*2,height))
  for i in range(0, len(shreds)):
    shred = shreds[i]
    orderedshred = orderedshreds[i]
    
    region = im.crop(shred)
    out.paste(region, orderedshred)
  return out

class Memoize:
  def __init__(self, f):
      self.f = f
      self.memo = {}
  def __call__(self, *args):
      if not args in self.memo:
          self.memo[args] = self.f(*args)
      return self.memo[args]
      
def memoize(f):
  cache={}
  def memf(*x):
    if x not in cache:
      cache[x] = f(*x)
    return cache[x]
  return memf

class PixelRow:
  def __init(v):
    self.v = v
  def get():
    return v
      
def getLeftPixels(pix, shred):
  rightmostBox = shred[-1]
  rightmostColumn = rightmostBox[2]-1
  pixels = []
  for i in range(0, rightmostBox[3]):
    pixels.append(pix[rightmostColumn, i])
  return PixelRow(pixels)

def getRightPixels(pix, shred):
  leftmostBox = shred[0]
  leftmostColumn = leftmostBox[0]
  pixels = []
  for i in range(0, leftmostBox[3]):
    pixels.append(pix[leftmostColumn, i])
  return PixelRow(pixels)
  
getLeftPixels = Memoize(getLeftPixels)
getRightPixels = Memoize(getRightPixels)

def score(pix, leftShred, rightShred):
  left = getLeftPixels(pix, leftShred).get()
  right = getRightPixels(pix, rightShred).get()
  diff = 0
  for l, r in zip(left, right):
    for c in range(0, 2):
      diff += abs(l[c] - r[c])
  return diff

def old_score(pix, leftShred, rightShred):
  leftBox = leftShred[-1]
  rightBox = rightShred[0]
  
  leftColumn = leftBox[2]-1
  rightColumn = rightBox[0]
  # loop through and calculate the sum of the differences of the left and right column pixels, pair by pair
  diff = 0
  for i in range(0, leftBox[3]):
    #print "left, right: ", leftColumn, rightColumn
    left = pix[leftColumn, i]
    right = pix[rightColumn, i]
    for c in range(0, 2):
      diff += abs(left[c] - right[c])
  #print "leftColumn: ", leftColumn, ", rightColumn: ", rightColumn, "score:", diff
  return diff

def scorePermutation(pix, permutation):
  diff = 0
  for i in range(0, len(permutation)-1):
    diff += score(pix, permutation[i], permutation[i+1])
  return diff

def findBestPermutation(pix, permutations):
  lowestScore = float('inf')
  lowestScorePermutation = None
  x = 0
  for permutation in permutations:
    x += 1
    #print "scoring shred, x:", x
    score = scorePermutation(pix, permutation)
    if score < lowestScore:
      lowestScore = score
      lowestScorePermutation = permutation
  #print "lowest: ", lowestScorePermutation, " score: ", lowestScore
  return lowestScorePermutation

def findAdjacentShreds(pix, metashreds, trycount):
  shredcount = len(metashreds)
  
  for tries in range(0,trycount):
    if(len(metashreds) == 1): break
    for i in range(0,shredcount):
      if(len(metashreds) == 1): break
      #print "metashreds count:", len(metashreds), " i:", i
      if(len(metashreds) >= i+1):
        reduceUsingAdjacentShreds(pix, metashreds, i)

def reduceUsingAdjacentShreds(pix, shreds, leftIdx):
  print "reducing left len:", len(shreds), " idx:", leftIdx
  lowestScore = float('inf')
  lowestScoreShred = None
  lowestScoreShredIdx = None
  leftShred = shreds[leftIdx]
  
  for i in range(0, len(shreds)):
    if(i == leftIdx): continue
    otherShred = shreds[i]
    s = score(pix, leftShred, otherShred)
    if s < lowestScore:
      lowestScore = s
      lowestScoreShred = otherShred
      lowestScoreShredIdx = i
  
  #print "lowestScore:", lowestScore
  if(lowestScore < 10000):
    combine(shreds, leftIdx, lowestScoreShredIdx)

def combine(shreds, leftShredIdx, rightShredIdx):
  print "combining left: ", leftShredIdx, " right: ", rightShredIdx, "combined:", shreds
  leftMetashred = shreds[leftShredIdx]
  rightMetashred = shreds.pop(rightShredIdx)
  leftMetashred.extend(rightMetashred)

# load source image
#im = Image.open("shredded3.png")
#im = Image.open("shredded6.png")
#im = Image.open("shredded10.png")
#im = Image.open("shredded15.png")
#im = Image.open("shredded.png")
im = Image.open("original.png")
print "bands: ", im.getbands
print "size: ", im.size[0], im.size[1]
print "format: ", im.format
print "mode: ", im.mode

# track some properties of the source image
width = im.size[0]
height = im.size[1]
pix = im.load()
print "0,0: ", pix[0,0]  # R,G,B,A for a single pixel
shredcount = 9 # 20
shredwidth = 25 # width/shredcount

#for shredcount in range(1,20):
for shredcount in range(19, 20):
  # find the shreads
  metashreds = []
  for i in range(0, shredcount):
    shred = (shredwidth*i, 0, shredwidth*(i+1), height)
    metashreds.append([shred])
    
  varient = copy.deepcopy(metashreds)
  iter = itertools.permutations(varient)
  permutationCount = random.randint(0,math.factorial(len(varient)) % 30493)
  orderedshreds = iter.next()
  for i in range(1, int(permutationCount)):
    try:
      orderedshreds = iter.next()
    except:
      break
  # display the image
  out = stitchTogether(im, metashreds, orderedshreds)
  out.show()
  # save the image
  out.save("shredded%s.png" % shredcount, "PNG")