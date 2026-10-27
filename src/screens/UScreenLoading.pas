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
 *
 * $URL: svn://basisbit@svn.code.sf.net/p/ultrastardx/svn/trunk/src/screens/UScreenLoading.pas $
 * $Id: UScreenLoading.pas 1939 2009-11-09 00:27:55Z s_alexander $
 *}

unit UScreenLoading;

interface

{$IFDEF FPC}
  {$MODE Delphi}
{$ENDIF}

{$I switches.inc}

uses
  UMenu,
  UMenuStatic,
  SysUtils,
  UThemes,
  sdl2;

type
  TRect4 = record
    X, Y, W, H: real;
  end;

  TScreenLoading = class(TMenu)
    private
      DiscoveryBarBaseIndex: integer;
      DiscoveryBarFillIndex: integer;
      LoadingBarBaseIndex: integer;
      LoadingBarFillIndex: integer;
      StatusTextIndex: integer;
      StatusTextBase: UTF8String;
      DiscoveryBarAlpha: real;
      LoadingBarAlpha: real;
      LastRedrawTicks: cardinal;
      // animated mark (see TThemeLoading.Mark*)
      StartTicks: cardinal;
      NoteBase: array of TRect4;
      LineBase, DotBase: TRect4;
      TextBaseY: array of real;
      procedure AnimateMark;
      procedure StoreMark;
      function ClampProgress(Current, Total: integer): real;
      function AddProgressOverlay(SourceBarIndex: integer; Alpha: real): integer;
      procedure UpdateBar(BaseBarIndex, FillBarIndex: integer; Progress, BaseAlpha, FillAlpha: real);
      procedure UpdateStatus(const Value: UTF8String);
    public
      Fadeout: boolean;
      TextDescription: integer;

      constructor Create; override;
      procedure OnShow; override;
      function Draw: boolean; override;
      function ParseInput(PressedKey: cardinal; CharCode: UCS4Char; PressedDown: boolean): boolean; override;
      procedure SetDiscoveryProgress(Current, Total, SongsFound: integer);
      procedure SetSongLoadingProgress(Current, Total: integer);
      procedure SetStatus(const Value: UTF8String);
      procedure RefreshProgress(Force: boolean = false);
  end;

implementation

uses
  Math,
  UGraphic,
  UDisplay,
  ULanguage,
  URenderer,
  UTime;

const
  // the empty part of a progress bar, relative to the filled part
  TrackAlpha = 0.25;

function TScreenLoading.ParseInput(PressedKey: cardinal; CharCode: UCS4Char; PressedDown: boolean): boolean;
begin
  Result := true;
end;

constructor TScreenLoading.Create;
begin
  inherited Create;

  LoadFromTheme(Theme.Loading);

  if Length(Statics) > 0 then
  begin
    DiscoveryBarBaseIndex := 0;
    DiscoveryBarAlpha := Statics[DiscoveryBarBaseIndex].Texture.Alpha;
    DiscoveryBarFillIndex := AddProgressOverlay(DiscoveryBarBaseIndex, DiscoveryBarAlpha);
  end
  else
  begin
    DiscoveryBarBaseIndex := -1;
    DiscoveryBarFillIndex := -1;
    DiscoveryBarAlpha := 1;
  end;

  if Length(Statics) > 1 then
  begin
    LoadingBarBaseIndex := 1;
    LoadingBarAlpha := Statics[LoadingBarBaseIndex].Texture.Alpha;
    LoadingBarFillIndex := AddProgressOverlay(LoadingBarBaseIndex, LoadingBarAlpha);
  end
  else
  begin
    LoadingBarBaseIndex := -1;
    LoadingBarFillIndex := -1;
    LoadingBarAlpha := 1;
  end;

  if Length(Text) > 0 then
  begin
    StatusTextIndex := 0;
    StatusTextBase := Text[0].Text;
  end
  else
  begin
    StatusTextIndex := -1;
    StatusTextBase := '';
  end;

  StoreMark;
  LastRedrawTicks := 0;
  UpdateBar(DiscoveryBarBaseIndex, DiscoveryBarFillIndex, 0, DiscoveryBarAlpha * TrackAlpha, DiscoveryBarAlpha);
  UpdateBar(LoadingBarBaseIndex, LoadingBarFillIndex, 0, LoadingBarAlpha * TrackAlpha, LoadingBarAlpha);
  UpdateStatus('');
  RefreshProgress(true);
  Fadeout := false;
end;

procedure TScreenLoading.OnShow;
begin
  inherited;
end;

function StaticRect(S: TStatic): TRect4;
begin
  Result.X := S.Texture.X;
  Result.Y := S.Texture.Y;
  Result.W := S.Texture.W;
  Result.H := S.Texture.H;
end;

procedure TScreenLoading.StoreMark;
var
  I: integer;
begin
  StartTicks := SDL_GetTicks();
  SetLength(NoteBase, Length(Theme.Loading.MarkNotes));
  for I := 0 to High(NoteBase) do
    if (Theme.Loading.MarkNotes[I] >= 0) and (Theme.Loading.MarkNotes[I] < Length(Statics)) then
      NoteBase[I] := StaticRect(Statics[Theme.Loading.MarkNotes[I]]);
  if (Theme.Loading.MarkLine >= 0) and (Theme.Loading.MarkLine < Length(Statics)) then
    LineBase := StaticRect(Statics[Theme.Loading.MarkLine]);
  if (Theme.Loading.MarkDot >= 0) and (Theme.Loading.MarkDot < Length(Statics)) then
    DotBase := StaticRect(Statics[Theme.Loading.MarkDot]);
  SetLength(TextBaseY, Length(Theme.Loading.MarkTexts));
  for I := 0 to High(TextBaseY) do
    if (Theme.Loading.MarkTexts[I] >= 0) and (Theme.Loading.MarkTexts[I] < Length(Text)) then
      TextBaseY[I] := Text[Theme.Loading.MarkTexts[I]].Y;
end;

const
  MARK_PERIOD = 2600;  // ms of one pass of the pitch marker
  MARK_INTRO = 700;    // ms of the fade in of the texts

{ the mark comes alive: the pitch marker runs over the note bars again and
  again, its dot rides on the bar under it, and each bar lights up and swells
  a little while it is being "sung"; the texts rise and fade in at the start }
procedure TScreenLoading.AnimateMark;
var
  T, P, MX, X1, X2, E, Lit, DotY, Swell: real;
  I, Under, Prev, Next: integer;
  Now: cardinal;
  S: TStatic;
  function NoteCY(N: integer): real;
  begin
    Result := NoteBase[N].Y + NoteBase[N].H / 2;
  end;
begin
  if (Length(NoteBase) = 0) or (Theme.Loading.MarkLine < 0) then
    Exit;
  Now := SDL_GetTicks();
  T := Now - StartTicks;

  // texts: rise and fade in
  E := Min(1, T / MARK_INTRO);
  E := 1 - (1 - E) * (1 - E) * (1 - E);
  for I := 0 to High(TextBaseY) do
    if (Theme.Loading.MarkTexts[I] >= 0) and (Theme.Loading.MarkTexts[I] < Length(Text)) then
    begin
      Text[Theme.Loading.MarkTexts[I]].Y := TextBaseY[I] + 14 * (1 - E);
      Text[Theme.Loading.MarkTexts[I]].Alpha := E;
    end;

  // marker position: from a bit before the first bar to a bit after the last
  X1 := NoteBase[0].X - 16;
  X2 := NoteBase[High(NoteBase)].X + NoteBase[High(NoteBase)].W + 16;
  P := Frac(T / MARK_PERIOD);
  // ease in and out, so it rests briefly at both ends
  P := P * P * (3 - 2 * P);
  MX := X1 + (X2 - X1) * P;

  // the bar under the marker (or the neighbours around it)
  Under := -1;
  Prev := -1;
  Next := -1;
  for I := 0 to High(NoteBase) do
  begin
    if (MX >= NoteBase[I].X) and (MX <= NoteBase[I].X + NoteBase[I].W) then
      Under := I;
    if (NoteBase[I].X + NoteBase[I].W < MX) then
      Prev := I;
    if (Next < 0) and (NoteBase[I].X > MX) then
      Next := I;
  end;
  if (Under >= 0) then
    DotY := NoteCY(Under)
  else if (Prev >= 0) and (Next >= 0) then
  begin
    E := (MX - (NoteBase[Prev].X + NoteBase[Prev].W)) / Max(1, NoteBase[Next].X - (NoteBase[Prev].X + NoteBase[Prev].W));
    E := E * E * (3 - 2 * E);
    DotY := NoteCY(Prev) + (NoteCY(Next) - NoteCY(Prev)) * E;
  end
  else if (Next >= 0) then
    DotY := NoteCY(Next)
  else
    DotY := NoteCY(High(NoteBase));

  // the bars: dim until the marker reaches them, lit after it, swelling
  // while it is on them; all fade back at the end of the pass
  for I := 0 to High(NoteBase) do
  begin
    if (Theme.Loading.MarkNotes[I] < 0) or (Theme.Loading.MarkNotes[I] >= Length(Statics)) then
      Continue;
    S := Statics[Theme.Loading.MarkNotes[I]];
    if (MX <= NoteBase[I].X) then
      Lit := 0
    else
      Lit := Min(1, (MX - NoteBase[I].X) / Max(1, NoteBase[I].W));
    Swell := 0;
    if (I = Under) then
      Swell := Sin(Pi * (MX - NoteBase[I].X) / Max(1, NoteBase[I].W));
    S.Texture.Alpha := 0.35 + 0.65 * Lit;
    S.Texture.H := NoteBase[I].H * (1 + 0.35 * Swell);
    S.Texture.W := NoteBase[I].W + 4 * Swell;
    S.Texture.X := NoteBase[I].X - 2 * Swell;
    S.Texture.Y := NoteBase[I].Y - (S.Texture.H - NoteBase[I].H) / 2;
  end;

  S := Statics[Theme.Loading.MarkLine];
  S.Texture.X := MX - LineBase.W / 2;
  if (Theme.Loading.MarkDot >= 0) and (Theme.Loading.MarkDot < Length(Statics)) then
  begin
    S := Statics[Theme.Loading.MarkDot];
    S.Texture.X := MX - DotBase.W / 2;
    S.Texture.Y := DotY - DotBase.H / 2;
  end;
end;

function TScreenLoading.Draw: boolean;
begin
  AnimateMark;
  Result := inherited Draw;
end;

function TScreenLoading.ClampProgress(Current, Total: integer): real;
begin
  if Total <= 0 then
    Result := 0
  else
    Result := Current / Total;

  if Result < 0 then
    Result := 0
  else if Result > 1 then
    Result := 1;
end;

function TScreenLoading.AddProgressOverlay(SourceBarIndex: integer; Alpha: real): integer;
var
  StaticNum: integer;
begin
  if (SourceBarIndex < 0) or (SourceBarIndex >= Length(Statics)) then
    Exit(-1);

  StaticNum := Length(Statics);
  SetLength(Statics, StaticNum + 1);
  Statics[StaticNum] := TStatic.Create(Statics[SourceBarIndex].Texture.Clone);
  Statics[StaticNum].Texture.Alpha := Alpha;
  Statics[StaticNum].Texture.W := 0;
  Statics[StaticNum].Visible := Statics[SourceBarIndex].Visible;
  Statics[StaticNum].Reflection := Statics[SourceBarIndex].Reflection;
  Statics[StaticNum].ReflectionSpacing := Statics[SourceBarIndex].ReflectionSpacing;
  Result := StaticNum;
end;

procedure TScreenLoading.UpdateBar(BaseBarIndex, FillBarIndex: integer; Progress, BaseAlpha, FillAlpha: real);
begin
  if (BaseBarIndex >= 0) and (BaseBarIndex < Length(Statics)) then
  begin
    Statics[BaseBarIndex].Texture.Alpha := BaseAlpha;
  end;

  if (FillBarIndex >= 0) and (FillBarIndex < Length(Statics)) then
  begin
    Statics[FillBarIndex].Texture.W := Progress * Statics[BaseBarIndex].Texture.W;
    Statics[FillBarIndex].Texture.Alpha := FillAlpha;
  end;
end;

procedure TScreenLoading.UpdateStatus(const Value: UTF8String);
begin
  if (StatusTextIndex >= 0) and (StatusTextIndex < Length(Text)) then
  begin
    if Value = '' then
      Text[StatusTextIndex].Text := StatusTextBase
    else
      Text[StatusTextIndex].Text := StatusTextBase + ' ' + Value;
  end;
end;

// the status line says what is happening in words: "Looking for songs ·
// 120 found", "Reading songs · 80 of 120"
procedure TScreenLoading.SetDiscoveryProgress(Current, Total, SongsFound: integer);
begin
  UpdateBar(DiscoveryBarBaseIndex, DiscoveryBarFillIndex, ClampProgress(Current, Total), DiscoveryBarAlpha * TrackAlpha, DiscoveryBarAlpha);
  if (StatusTextIndex >= 0) then
  begin
    if SongsFound > 0 then
      Text[StatusTextIndex].Text := Format(Language.Translate('LOADING_FOUND'), [SongsFound])
    else
      Text[StatusTextIndex].Text := Language.Translate('LOADING_SEARCHING');
  end;
  RefreshProgress;
end;

procedure TScreenLoading.SetSongLoadingProgress(Current, Total: integer);
begin
  UpdateBar(LoadingBarBaseIndex, LoadingBarFillIndex, ClampProgress(Current, Total), LoadingBarAlpha * TrackAlpha, LoadingBarAlpha);
  if (StatusTextIndex >= 0) then
  begin
    if Total > 0 then
      Text[StatusTextIndex].Text := Format(Language.Translate('LOADING_SONGS'), [Current, Total])
    else
      Text[StatusTextIndex].Text := StatusTextBase;
  end;
  RefreshProgress;
end;

// steps of the start (e.g. "Loading ScreenSong") are not shown, they mean
// nothing to the player
procedure TScreenLoading.SetStatus(const Value: UTF8String);
begin
  if (StatusTextIndex >= 0) and (StatusTextIndex < Length(Text)) then
    Text[StatusTextIndex].Text := StatusTextBase;
  RefreshProgress(true);
end;

procedure TScreenLoading.RefreshProgress(Force: boolean);
var
  NowTicks: cardinal;
begin
  if (Display = nil) or (Display.CurrentScreen <> @ScreenLoading) then
    Exit;

  NowTicks := SDL_GetTicks;
  if not Force and (LastRedrawTicks <> 0) and (NowTicks - LastRedrawTicks < 30) then
    Exit;

  Self.Draw;
  Display.Draw;
  Renderer.SwapBuffers;
  LastRedrawTicks := NowTicks;
end;

end.
