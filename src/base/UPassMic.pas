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

unit UPassMic;

{ "Pass the mic" for the normal game: everybody present takes a turn.

  It is the Team Duel party mode (game/plugins/teamduel.usdx) without teams
  or names. While the song plays, a banner warns before each change and
  flashes when it happens. The changes are spread the same way as in the
  plugin: one every 6 to 12 percent of the points of the song, so the
  singing time between two of them depends on the song. }

interface

{$IFDEF FPC}
  {$MODE Delphi}
{$ENDIF}

{$I switches.inc}

type
  TPassMic = class
    private
      fChanges: array of real; // time of each change, in seconds
      fNext: integer;          // index of the next change
      fLastChange: real;       // time of the change that just happened
    public
      { calculates the changes of the loaded song; call it once it is loaded.
        Active is false when the mode does not apply (a medley plays only
        part of each song). }
      procedure Prepare(Active: boolean);
      { draws the banner; Time is the current lyrics time in seconds }
      procedure Draw(Time: real);
  end;

var
  PassMic: TPassMic;

implementation

uses
  Math,
  SysUtils,
  UGraphic,
  UIni,
  ULanguage,
  UMusic,
  UNote,
  UThemes,
  URenderer,
  USong,
  UText;

const
  MIN_PERCENTAGE = 0.06; // same limits as the Team Duel plugin
  MAX_PERCENTAGE = 0.12;
  WARN_SECONDS   = 6;    // the banner shows this long before the change
  NOW_SECONDS    = 1.5;  // and this long after it

procedure TPassMic.Prepare(Active: boolean);
var
  LineStart: array of integer; // start beat of every line of every track
  LineValue: array of integer; // its points, in note beats
  Order: array of integer;
  Track, Line, Note, Count, I, J, Tmp: integer;
  Total, Beats, ToChange: integer;

  function Step: integer;
  begin
    Result := Max(1, Ceil((MIN_PERCENTAGE + (MAX_PERCENTAGE - MIN_PERCENTAGE) * Random) * Total));
  end;

begin
  SetLength(fChanges, 0);
  fNext := 0;
  fLastChange := -1000;
  if (not Active) or (Ini.PassMic = 0) or (CurrentSong = nil) then
    Exit;

  // gather the lines of all the tracks (a duet has two)
  Count := 0;
  Total := 0;
  for Track := 0 to High(CurrentSong.Tracks) do
  begin
    SetLength(LineStart, Count + Length(CurrentSong.Tracks[Track].Lines));
    SetLength(LineValue, Length(LineStart));
    for Line := 0 to High(CurrentSong.Tracks[Track].Lines) do
    with CurrentSong.Tracks[Track].Lines[Line] do
    begin
      LineStart[Count] := StartBeat;
      LineValue[Count] := 0;
      for Note := 0 to High(Notes) do
        Inc(LineValue[Count], Notes[Note].Duration * ScoreFactor[Notes[Note].NoteType]);
      Inc(Total, LineValue[Count]);
      Inc(Count);
    end;
  end;
  if (Count < 2) or (Total = 0) then
    Exit;

  // sort the lines by start beat
  SetLength(Order, Count);
  for I := 0 to Count - 1 do
    Order[I] := I;
  for I := 1 to Count - 1 do
  begin
    Tmp := Order[I];
    J := I - 1;
    while (J >= 0) and (LineStart[Order[J]] > LineStart[Tmp]) do
    begin
      Order[J + 1] := Order[J];
      Dec(J);
    end;
    Order[J + 1] := Tmp;
  end;

  // a change at the line after the one where the points since the last one
  // reach the step, once those points have been sung
  Beats := 0;
  ToChange := Step;
  for I := 0 to Count - 2 do // never at the last line: nobody would sing it
  begin
    Inc(Beats, LineValue[Order[I]]);
    if Beats >= ToChange then
    begin
      SetLength(fChanges, Length(fChanges) + 1);
      fChanges[High(fChanges)] := GetTimeFromBeat(LineStart[Order[I + 1]]);
      Inc(ToChange, Step);
    end;
  end;
end;

procedure TPassMic.Draw(Time: real);
const
  BAR_W = 360;
  BAR_H = 52;
  TOP   = 28;
var
  ToNext, Progress, Alpha: real;
  AccR, AccG, AccB, TxtR, TxtG, TxtB: real;
  Msg: UTF8String;
  X, W: real;
begin
  // the song was restarted
  while (fNext > 0) and (fChanges[fNext - 1] > Time) do
  begin
    Dec(fNext);
    fLastChange := -1000;
  end;

  // changes already behind (a seek, or the song opened late) pass silently
  while (fNext < Length(fChanges)) and (fChanges[fNext] <= Time) do
  begin
    fLastChange := fChanges[fNext];
    Inc(fNext);
  end;

  if fNext < Length(fChanges) then
    ToNext := fChanges[fNext] - Time
  else
    ToNext := 1000;

  if (Time >= fLastChange) and (Time - fLastChange < NOW_SECONDS) then
  begin
    Msg := Language.Translate('SING_PASSMIC_NOW');
    Progress := 1;
    Alpha := 1 - Max(0, (Time - fLastChange) / NOW_SECONDS - 0.6) / 0.4;
  end
  else if (ToNext > 0) and (ToNext <= WARN_SECONDS) then
  begin
    Msg := Language.Translate('SING_PASSMIC_NEXT');
    Progress := 1 - ToNext / WARN_SECONDS;
    Alpha := Min(1, (WARN_SECONDS - ToNext) * 4);
  end
  else
    Exit;

  // colours of the theme: the same accent as the selected options
  AccR := 1; AccG := 0.78; AccB := 0.2; // for a theme without Accent
  TxtR := 1; TxtG := 1; TxtB := 1;
  LoadColor(AccR, AccG, AccB, 'Accent');
  LoadColor(TxtR, TxtG, TxtB, 'Text');

  X := (RenderW - BAR_W) / 2;
  Renderer.DrawQuad(X, TOP, 0, BAR_W, BAR_H, 0, 0, 0, 0.72 * Alpha);
  Renderer.DrawQuad(X + 4, TOP + BAR_H - 10, 0, (BAR_W - 8) * Progress, 6, AccR, AccG, AccB, Alpha);

  SetFontFamily(0);
  SetFontStyle(ftBold);
  SetFontItalic(false);
  SetFontSize(24);
  W := TextWidth(PChar(Msg));
  if (W > BAR_W - 24) then // long translations shrink to fit
  begin
    SetFontSize(24 * (BAR_W - 24) / W);
    W := TextWidth(PChar(Msg));
  end;
  SetFontColor(TxtR, TxtG, TxtB, Alpha);
  SetFontPos(RenderW / 2 - W / 2, TOP + 6);
  PrintText(PChar(Msg));
end;

initialization
  PassMic := TPassMic.Create;

finalization
  PassMic.Free;

end.
