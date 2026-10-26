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
 * $URL: svn://basisbit@svn.code.sf.net/p/ultrastardx/svn/trunk/src/menu/UMenuText.pas $
 * $Id: UMenuText.pas 2293 2010-04-23 22:39:26Z tobigun $
 *}

unit UMenuText;

interface

{$IFDEF FPC}
  {$MODE Delphi}
{$ENDIF}

{$I switches.inc}

uses
  math,
  SysUtils,
  sdl2,
  UText,
  UMenuInteract;

type
  TText = class
    private
      SelectBool:  boolean;
      TextString:  UTF8String;
      TextTiles:   array of UTF8String;

      STicks:      cardinal;
      SelectBlink: boolean;
      AnimStart:   cardinal;   // colour transition between Color and DColor
    public
      X:       single;
      Y:       single;
      Z:       single;
      MoveX:   single;       // some modifier for x - position that don't affect the single Y
      MoveY:   single;       // some modifier for y - position that don't affect the single Y
      W:       single;       // text wider than W is wrapped
      H:       single;       // text higher than H is decreased in font size
      Size:    single;
      ColR:    single;
      ColG:    single;
      ColB:    single;
      // colour while the text's button is not selected (themes: DColor of a
      // button text); only used when UseDColor is set
      DColR, DColG, DColB: single;
      UseDColor: boolean;

      Alpha:   single;
      Int:     single;
      Font:    integer;
      Style:   integer;
      Visible: boolean;
      Align:   integer; // 0 = left, 1 = center, 2 = right

      // reflection
      Reflection:        boolean;
      ReflectionSpacing: single;

      Writable: boolean;

      // with W and H set, long texts get smaller down to MinSize; below
      // that they are cut with "..." (0: no limit)
      MinSize: single;

      function LineCount: integer;

      procedure SetSelect(Value: boolean);
      property Selected: boolean read SelectBool write SetSelect;

      procedure SetText(Value: UTF8String);
      property  Text: UTF8String read TextString write SetText;

      procedure DeleteLastLetter; //< Deletes the rightmost letter

      procedure Draw;
      constructor Create; overload;
      constructor Create(X, Y: single; const Text: UTF8String); overload;
      constructor Create(ParX, ParY, ParW, ParH: single; ParFont, ParStyle: integer; ParSize, ParColR, ParColG, ParColB: single; ParAlign: integer; const ParText: UTF8String; ParReflection: boolean; ParReflectionSpacing: single; ParZ: single; Writable: boolean); overload;

      function GetMouseOverArea: TMouseOverRect;
  end;

implementation

uses
  UGraphic,
  UDisplay,
  UUnicodeStringHelper,
  UUnicodeUtils,
  StrUtils;

procedure TText.SetSelect(Value: boolean);
begin
  if UseDColor and (Value <> SelectBool) then
  begin
    AnimStart := SDL_GetTicks();
    if (AnimStart = 0) then
      AnimStart := 1;
  end;
  SelectBool := Value;

  // set cursor visible
  SelectBlink := true;
  STicks := SDL_GetTicks() div 550;
end;

procedure TText.SetText(Value: UTF8String);
var
  NextPos:     cardinal;  // next pos of a space etc.
  LastPos:     cardinal;  // last pos "
  LastBreak:   cardinal;  // last break
  isBreak:     boolean;   // true if the break is not caused because the text is out of the area
  FirstWord:   word;      // is first word after break?
  Len:         word;      // length of the tiles array
  DecFontSize: boolean = true; // how to handle strings that are too long to fit a given height, either decrease font size or cut off with ellipsis

  function GetNextPos: boolean;
  var
    T1, {T2,} T3: cardinal;
  begin
    LastPos := NextPos;

    // next space (if width is given)
    if (W > 0) then
      T1 := PosEx(' ', Value, LastPos + 1)
    else
      T1 := Length(Value);

    {// next -
    T2 := PosEx('-', Value, LastPos + 1);}

    // next break
    T3 := PosEx('\n', Value, LastPos + 1);

    if T1 = 0 then
      T1 := Length(Value);
    {if T2 = 0 then
      T2 := Length(Value); }
    if T3 = 0 then
      T3 := Length(Value);

    // get nearest pos
    NextPos := min(T1, T3{min(T2, T3)});

    if (LastPos = cardinal(Length(Value))) then
      NextPos := 0;

    isBreak := (NextPos = T3) and (NextPos <> cardinal(Length(Value)));
    Result := (NextPos <> 0);
  end;

  procedure AddBreak(const From, bTo: cardinal);
  begin
    if (isBreak) or (bTo - From >= 1) then
    begin
      Inc(Len);
      SetLength (TextTiles, Len);
      TextTiles[Len-1] := Trim(Copy(Value, From, bTo - From));

      if isBreak then
        LastBreak := bTo + 2
      else
        LastBreak := bTo + 1;
      FirstWord := 0;
    end;
  end;

begin
  isBreak := false;
  // set TextString
  TextString := Value;

  // set cursor visible
  SelectBlink := true;
  STicks := SDL_GetTicks() div 550;

  // exit if there is no need to create tiles
  if (W <= 0) and (Pos('\n', Value) = 0) then
  begin
    SetLength (TextTiles, 1);
    TextTiles[0] := Value;
    Exit;
  end;

  // create tiles
  // reset text array
  SetLength (TextTiles, 0);
  Len := 0;

  // reset counter vars
  LastPos := 1;
  NextPos := 1;
  LastBreak := 1;
  FirstWord := 1;

  if (W > 0) then
  begin
    // set font properties
    SetFontFamily(Font);
    SetFontStyle(Style);
    SetFontSize(Size);
  end;

  // go through text
  while (GetNextPos) do
  begin
      // break in text
      if isBreak then
      begin
        // look for break before the break
        if (TextWidth(Copy(Value, LastBreak, NextPos - LastBreak + 1)) > W) AND (NextPos-LastPos > 1) then
        begin
          isBreak := false;
          // not the first word after break, so we don't have to break within a word
          if (FirstWord > 1) then
          begin
            // add break before actual position, because there the text fits the area
            AddBreak(LastBreak, LastPos);
          end
          else // first word after break break within the word
          begin
            // to do
            // AddBreak(LastBreak, LastBreak + 155);
          end;
        end;

        isBreak := true;
        // add break from text
        AddBreak(LastBreak, NextPos);
      end
      // text comes out of the text area -> createbreak
      else if (TextWidth(Copy(Value, LastBreak, NextPos - LastBreak + 1)) > W) then
      begin
        // not the first word after break, so we don't have to break within a word
        if (FirstWord > 1) then
        begin
          // add break before actual position, because there the text fits the area
          AddBreak(LastBreak, LastPos);
        end
        else // first word after break -> break within the word
        begin
          // to do
          // AddBreak(LastBreak, LastBreak + 155);
        end;
      end;
    //end;
    Inc(FirstWord)
  end;
  // add ending
  AddBreak(LastBreak, Length(Value)+1);

  // if a height is given, there are only two ugly solutions (but prettier than overlapping text, e.g. artist/title in song menu)
  // a) decrease font size
  // b) cut off the last lines
  // until the text fits within the given height
  if (H > 0) and (Len * Size > H) then
  begin
    if DecFontSize and not ((MinSize > 0) and (Size - 1 < MinSize)) then
    begin
      Size := Size - 1; // round(Size * 0.95 * 10) / 10;
      SetText(Value);
    end
    else
    begin
      Len := Max(1, trunc(H / Size));
      SetLength(TextTiles, Len);
      // make room for the dots
      if (W > 0) then
      begin
        SetFontFamily(Font);
        SetFontStyle(Style);
        SetFontSize(Size);
        while (Length(TextTiles[Len-1]) > 1) and (TextWidth(TextTiles[Len-1] + '...') > W) do
          TextTiles[Len-1] := UTF8Copy(TextTiles[Len-1], 1, LengthUTF8(TextTiles[Len-1]) - 1);
        TextTiles[Len-1] := TrimRight(TextTiles[Len-1]);
      end;
      TextTiles[Len-1] := TextTiles[Len-1] + '...';
    end;
  end;
end;

function TText.LineCount: integer;
begin
  Result := Length(TextTiles);
end;

procedure TText.DeleteLastLetter;
begin
  SetText(UTF8Copy(TextString, 1, LengthUTF8(TextString)-1));
end;

procedure TText.Draw;
var
  E:      single;
  X2, Y2: single;
  tmpText2, Text2:  UTF8String;
  I:      integer;
  Ticks:  cardinal;
begin
  if Visible then
  begin
    SetFontFamily(Font);
    SetFontStyle(Style);
    SetFontSize(Size);
    SetFontItalic(false);

    if UseDColor and (AnimStart <> 0) then
    begin
      // ease from the other colour to the current one
      E := (SDL_GetTicks() - AnimStart) / 140;
      if (E >= 1) then
      begin
        AnimStart := 0;
        E := 1;
      end
      else
        E := 1 - (1 - E) * (1 - E) * (1 - E);
      if not SelectBool then
        E := 1 - E; // E: share of the selected colour
      SetFontColor((DColR + (ColR - DColR) * E) * Int, (DColG + (ColG - DColG) * E) * Int,
                   (DColB + (ColB - DColB) * E) * Int, Alpha);
    end
    else if UseDColor and not SelectBool then
      SetFontColor(DColR*Int, DColG*Int, DColB*Int, Alpha)
    else
      SetFontColor(ColR*Int, ColG*Int, ColB*Int, Alpha);

    // reflection
    if Reflection then
      SetFontReflection(true, ReflectionSpacing)
    else
      SetFontReflection(false,0);

    // if selected set blink...
    if SelectBool then
    begin
      Ticks := SDL_GetTicks() div 550;
      if Ticks <> STicks then
      begin // change visability
        STicks := Ticks;
        SelectBlink := Not SelectBlink;
      end;
    end;

    {if (false) then // no width set draw as one long string
    begin
      if not (SelectBool AND SelectBlink) then
        Text2 := Text
      else
        Text2 := Text + '|';

      case Align of
        0: X2 := X;
        1: X2 := X - TextWidth(Text2)/2;
        2: X2 := X - TextWidth(Text2);
      end;

      SetFontPos(X2, Y);
      PrintText(Text2);
      SetFontStyle(ftNormal); // reset to default
    end
    else
    begin}
    // now use always:
    // draw text as many strings
      Y2 := Y + MoveY;
      for I := 0 to High(TextTiles) do
      begin
        tmpText2 := TextTiles[I];

        if (not (SelectBool and SelectBlink)) or (I <> High(TextTiles)) then
        begin
          Text2 := TextTiles[I];
        end
        else
        begin
          if (Writable) then
            Text2 := TextTiles[I] + '|'
          else
            Text2 := TextTiles[I];
        end;

        case Align of
          1: X2 := X + MoveX - TextWidth(tmpText2)/2; { centered }
          2: X2 := X + MoveX - TextWidth(tmpText2); { right aligned }
          else X2 := X + MoveX; { left aligned (default) }
        end;

        SetFontPos(X2, Y2);

        SetFontZ(Z);

        PrintText(Text2);

        {if Size >= 10 then
          Y2 := Y2 + Size * 0.93
        else}
        if (Style = ftBold) then
          Y2 := Y2 + Size * 0.93
        else
          Y2 := Y2 + Size * 0.85;
      end;

      // reset to default
      SetFontFamily(0);
      SetFontStyle(ftRegular);

    //end;
  end;
end;

constructor TText.Create;
begin
  Create(0, 0, '');
end;

constructor TText.Create(X, Y: single; const Text: UTF8String);
begin
  Create(X, Y, 0, 0, 0, ftRegular, 30, 0, 0, 0, 0, Text, false, 0, 0, false);
end;

constructor TText.Create(ParX, ParY, ParW, ParH: single;
                         ParFont, ParStyle: integer;
                         ParSize, ParColR, ParColG, ParColB: single;
                         ParAlign: integer;
                         const ParText: UTF8String;
                         ParReflection: boolean;
                         ParReflectionSpacing: single;
                         ParZ: single;
                         Writable: boolean);
begin
  inherited Create;
  Alpha := 1;
  X := ParX;
  Y := ParY;
  W := ParW;
  H := ParH;
  Z := ParZ;
  Font := ParFont;
  Style := ParStyle;
  Size := ParSize;
  Text := ParText;
  ColR := ParColR;
  ColG := ParColG;
  ColB := ParColB;
  Int := 1;
  Align := ParAlign;
  SelectBool := false;
  Visible := true;
  Reflection := ParReflection;
  ReflectionSpacing := ParReflectionSpacing;
  Writable := Writable;
end;

function TText.GetMouseOverArea: TMouseOverRect;
begin
  if not(Display.Cursor_HiddenByScreen) then
  begin
    if (Align = 0) then
    begin
      Result.X := X;
      Result.Y := Y;
      Result.W := TextWidth(Text);
      Result.H := Size;
    end;

    if (Align = 1) then
    begin
      Result.X := X -TextWidth(Text)/2;
      Result.Y := Y;
      Result.W := TextWidth(Text);
      Result.H := Size;
    end;

    if (Align = 2) then
    begin
      if (W <> 0) then
        Result.X := X - W
      else
        Result.X := X - TextWidth(Text);

      Result.Y := Y;

      if (W <> 0) then
        Result.W := W
      else
        Result.W := TextWidth(Text);

      Result.H := Size;
    end;
  end;
end;

end.
