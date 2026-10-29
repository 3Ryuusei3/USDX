{* UltraStar Deluxe - Karaoke Game
 *
 * UltraStar Deluxe is the legal property of its developers, whose names
 * are too numerous to list here. Please refer to the COPYRIGHT
 * file distributed with this source distribution.
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; see the file COPYING. If not, write to
 * the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
 * Boston, MA 02110-1301, USA.
 *}

unit UCoverLoader;

{ Song covers for the song selection, loaded without blocking the screen.

  Reading and decoding a cover (often a big JPEG, maybe on a slow external
  disk) took long enough to make the song menu stutter on every move. Here a
  background thread reads, decodes and shrinks the images; the main thread
  only uploads the small result to the GPU (Poll) and keeps the textures in
  a cache, so moving back and forth costs nothing.

  The cache owns the textures; Get hands out clones (they share the GPU
  texture and do not free it). }

interface

{$IFDEF FPC}
  {$MODE Delphi}
{$ENDIF}

{$I switches.inc}

uses
  Classes,
  SysUtils,
  sdl2,
  UPath,
  URenderer;

type
  { tells the owner that a cached texture is about to be freed, so it can
    drop the clones it handed out }
  TCoverEvictEvent = procedure(const Name: string) of object;
  { asks the owner whether a cover is still on screen (not evicted then) }
  TCoverInUseFunc = function(const Name: string): boolean of object;

  TCoverEntry = class
    Tex: TTexture;
    Stamp: cardinal;
  end;

  TCoverLoader = class
  private
    fLock: PSDL_Mutex;
    fWake: PSDL_Cond;
    fThread: PSDL_Thread;
    fQuit: boolean;
    fQueue: TStringList;     // requested, newest last (loaded first)
    fBusy: string;           // being loaded by the thread
    fDone: TStringList;      // loaded, Objects = PSDL_Surface
    fCache: TStringList;     // sorted, Objects = TCoverEntry
    fClock: cardinal;
    fMaxSize: integer;
    fMaxCount: integer;
    fSquare: boolean;        // crop to a centred square
    fRadius: real;           // rounded corners, fraction of the side (0 = none)
    procedure Evict;
    procedure Shape(var Surface: PSDL_Surface);
  public
    OnEvict: TCoverEvictEvent;
    InUse: TCoverInUseFunc;
    constructor Create(MaxSize, MaxCount: integer);
    destructor Destroy; override;
    { main thread: a clone of the cached cover, or nil (then it is requested) }
    function Get(const Name: IPath): TTexture;
    function IsCached(const Name: IPath): boolean;
    procedure Request(const Name: IPath);
    { how covers are cut (from the theme); a change empties the cache }
    procedure SetShape(Square: boolean; Radius: real);
    { main thread: upload what the loader finished; true if anything new }
    function Poll: boolean;
    { worker }
    procedure Run;
  end;

var
  CoverLoader: TCoverLoader;

implementation

uses
  Math,
  ULog,
  UImage;

const
  MAX_QUEUE = 48;

type
  // gives access to TRenderer's protected LoadTexture(Data, ...)
  TRendererAccess = class(TRenderer);

procedure RoundCorners(Surface: PSDL_Surface; Radius: real); forward;

function CoverThreadMain(Data: Pointer): integer; cdecl;
begin
  TCoverLoader(Data).Run;
  Result := 0;
end;

constructor TCoverLoader.Create(MaxSize, MaxCount: integer);
begin
  inherited Create;
  fMaxSize := MaxSize;
  fMaxCount := MaxCount;
  fQueue := TStringList.Create;
  fDone := TStringList.Create;
  fCache := TStringList.Create;
  fCache.Sorted := true;
  fCache.CaseSensitive := true;
  fCache.Duplicates := dupIgnore;
  fLock := SDL_CreateMutex();
  fWake := SDL_CreateCond();
  fThread := SDL_CreateThread(@CoverThreadMain, 'USDX covers', Self);
end;

destructor TCoverLoader.Destroy;
var
  I: integer;
begin
  SDL_LockMutex(fLock);
  fQuit := true;
  SDL_CondSignal(fWake);
  SDL_UnlockMutex(fLock);
  if (fThread <> nil) then
    SDL_WaitThread(fThread, nil);
  SDL_DestroyCond(fWake);
  SDL_DestroyMutex(fLock);
  for I := 0 to fDone.Count - 1 do
    SDL_FreeSurface(PSDL_Surface(fDone.Objects[I]));
  for I := 0 to fCache.Count - 1 do
  begin
    TCoverEntry(fCache.Objects[I]).Tex.Free;
    fCache.Objects[I].Free;
  end;
  fQueue.Free;
  fDone.Free;
  fCache.Free;
  inherited;
end;

procedure TCoverLoader.Run;
var
  Name: string;
  Surface: PSDL_Surface;
  Scale: real;
begin
  while true do
  begin
    SDL_LockMutex(fLock);
    while (not fQuit) and (fQueue.Count = 0) do
      SDL_CondWait(fWake, fLock);
    if fQuit then
    begin
      SDL_UnlockMutex(fLock);
      Exit;
    end;
    Name := fQueue[fQueue.Count - 1];
    fQueue.Delete(fQueue.Count - 1);
    fBusy := Name;
    SDL_UnlockMutex(fLock);

    Surface := nil;
    try
      Surface := LoadImage(Path(Name));
      if (Surface <> nil) then
      begin
        if fSquare and (Surface.W <> Surface.H) then
          Shape(Surface);
        if (Max(Surface.W, Surface.H) > fMaxSize) then
        begin
          Scale := Max(Surface.W, Surface.H) / fMaxSize;
          ScaleImage(Surface, Max(1, Floor(Surface.W / Scale)), Max(1, Floor(Surface.H / Scale)));
        end;
        if (fRadius > 0) then
        begin
          AdjustPixelFormat(Surface, TEXTURE_TYPE_TRANSPARENT);
          RoundCorners(Surface, fRadius);
        end
        else
          AdjustPixelFormat(Surface, TEXTURE_TYPE_PLAIN);
      end;
    except
      on E: Exception do
      begin
        Log.LogError('Cover ' + Name + ': ' + E.Message, 'TCoverLoader.Run');
        Surface := nil;
      end;
    end;

    SDL_LockMutex(fLock);
    fBusy := '';
    // also a failed load is reported (nil), so it is not requested again
    fDone.AddObject(Name, TObject(Surface));
    SDL_UnlockMutex(fLock);
  end;
end;

{ cuts the middle square out of the image }
procedure TCoverLoader.Shape(var Surface: PSDL_Surface);
var
  Side: integer;
  Src: TSDL_Rect;
  Square: PSDL_Surface;
begin
  Side := Min(Surface.W, Surface.H);
  Src.x := (Surface.W - Side) div 2;
  Src.y := (Surface.H - Side) div 2;
  Src.w := Side;
  Src.h := Side;
  Square := SDL_CreateRGBSurfaceWithFormat(0, Side, Side, 32, SDL_PIXELFORMAT_RGBA32);
  if (Square = nil) then
    Exit;
  SDL_SetSurfaceBlendMode(Surface, SDL_BLENDMODE_NONE);
  if (SDL_BlitSurface(Surface, @Src, Square, nil) <> 0) then
  begin
    SDL_FreeSurface(Square);
    Exit;
  end;
  SDL_FreeSurface(Surface);
  Surface := Square;
end;

{ transparent, antialiased corners (RGBA32 surface) }
procedure RoundCorners(Surface: PSDL_Surface; Radius: real);
var
  R, D, Cov: real;
  X, Y, CX, CY, N: integer;
  Row: PByte;
begin
  R := Radius * Min(Surface.W, Surface.H);
  N := Ceil(R);
  if (N <= 0) then
    Exit;
  SDL_LockSurface(Surface);
  for Y := 0 to Surface.H - 1 do
  begin
    if (Y >= N) and (Y < Surface.H - N) then
      Continue;
    Row := PByte(Surface.pixels) + Y * Surface.pitch;
    for X := 0 to Surface.W - 1 do
    begin
      if (X >= N) and (X < Surface.W - N) then
        Continue;
      // the centre of the corner's circle
      if (X < N) then CX := N else CX := Surface.W - N;
      if (Y < N) then CY := N else CY := Surface.H - N;
      D := Sqrt(Sqr(X + 0.5 - CX) + Sqr(Y + 0.5 - CY));
      Cov := R - D + 0.5;
      if (Cov >= 1) then
        Continue;
      if (Cov < 0) then
        Cov := 0;
      (Row + X * 4 + 3)^ := Round((Row + X * 4 + 3)^ * Cov);
    end;
  end;
  SDL_UnlockSurface(Surface);
end;

procedure TCoverLoader.SetShape(Square: boolean; Radius: real);
var
  I: integer;
begin
  if (Square = fSquare) and (Abs(Radius - fRadius) < 0.0001) then
    Exit;
  SDL_LockMutex(fLock);
  fSquare := Square;
  fRadius := Radius;
  fQueue.Clear;
  for I := 0 to fDone.Count - 1 do
    SDL_FreeSurface(PSDL_Surface(fDone.Objects[I]));
  fDone.Clear;
  SDL_UnlockMutex(fLock);
  for I := 0 to fCache.Count - 1 do
  begin
    TCoverEntry(fCache.Objects[I]).Tex.Free;
    fCache.Objects[I].Free;
  end;
  fCache.Clear;
end;

function TCoverLoader.IsCached(const Name: IPath): boolean;
begin
  Result := fCache.IndexOf(Name.ToNative) >= 0;
end;

function TCoverLoader.Get(const Name: IPath): TTexture;
var
  I: integer;
  E: TCoverEntry;
begin
  Result := nil;
  if (Name = nil) or Name.IsUnset then
    Exit;
  I := fCache.IndexOf(Name.ToNative);
  if (I >= 0) then
  begin
    E := TCoverEntry(fCache.Objects[I]);
    Inc(fClock);
    E.Stamp := fClock;
    if (E.Tex <> nil) then
      Result := E.Tex.Clone();
  end
  else
    Request(Name);
end;

procedure TCoverLoader.Request(const Name: IPath);
var
  S: string;
  I: integer;
begin
  if (Name = nil) or Name.IsUnset then
    Exit;
  S := Name.ToNative;
  if (fCache.IndexOf(S) >= 0) then
    Exit;
  SDL_LockMutex(fLock);
  if (S <> fBusy) and (fDone.IndexOf(S) < 0) then
  begin
    // move to the end: the latest requests are loaded first
    I := fQueue.IndexOf(S);
    if (I >= 0) then
      fQueue.Delete(I);
    fQueue.Add(S);
    // covers requested long ago have scrolled away
    while (fQueue.Count > MAX_QUEUE) do
      fQueue.Delete(0);
    SDL_CondSignal(fWake);
  end;
  SDL_UnlockMutex(fLock);
end;

procedure TCoverLoader.Evict;
var
  I, Victim: integer;
  Oldest: cardinal;
  E: TCoverEntry;
begin
  while (fCache.Count > fMaxCount) do
  begin
    Victim := -1;
    Oldest := High(cardinal);
    for I := 0 to fCache.Count - 1 do
    begin
      E := TCoverEntry(fCache.Objects[I]);
      if (E.Stamp < Oldest) and not (Assigned(InUse) and InUse(fCache[I])) then
      begin
        Oldest := E.Stamp;
        Victim := I;
      end;
    end;
    if (Victim < 0) then
      Exit;
    if Assigned(OnEvict) then
      OnEvict(fCache[Victim]);
    E := TCoverEntry(fCache.Objects[Victim]);
    E.Tex.Free;
    E.Free;
    fCache.Delete(Victim);
  end;
end;

function TCoverLoader.Poll: boolean;
var
  Done: TStringList;
  I: integer;
  Surface: PSDL_Surface;
  E: TCoverEntry;
  Typ: TTextureType;
begin
  Result := false;
  if (fDone.Count = 0) then // a racy peek is fine here
    Exit;
  Done := TStringList.Create;
  SDL_LockMutex(fLock);
  Done.Assign(fDone);
  fDone.Clear;
  SDL_UnlockMutex(fLock);

  for I := 0 to Done.Count - 1 do
  begin
    Surface := PSDL_Surface(Done.Objects[I]);
    E := TCoverEntry.Create;
    E.Tex := nil;
    if (Surface <> nil) then
    begin
      SDL_LockSurface(Surface);
      if (Surface^.format^.BytesPerPixel = 4) then
        Typ := TEXTURE_TYPE_TRANSPARENT
      else
        Typ := TEXTURE_TYPE_PLAIN;
      E.Tex := TRendererAccess(Renderer).LoadTexture(PByte(Surface^.pixels), Surface^.w, Surface^.h, Path(Done[I]),
                                    Typ, true);
      SDL_FreeSurface(Surface);
    end;
    Inc(fClock);
    E.Stamp := fClock;
    if (fCache.IndexOf(Done[I]) >= 0) then
    begin
      E.Tex.Free;
      E.Free;
    end
    else
      fCache.AddObject(Done[I], E);
    Result := true;
  end;
  Done.Free;
  Evict;
end;

end.
