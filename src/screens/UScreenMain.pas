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
 * $URL: svn://basisbit@svn.code.sf.net/p/ultrastardx/svn/trunk/src/screens/UScreenMain.pas $
 * $Id: UScreenMain.pas 3128 2015-08-28 01:45:23Z basisbit $
 *}

unit UScreenMain;

interface

{$IFDEF FPC}
  {$MODE Delphi}
{$ENDIF}

{$I switches.inc}

uses
  UConfig,
  UDisplay,
  UFiles,
  UMenu,
  UMusic,
  UScreenSong,
  USong,
  UThemes,
  MD5,
  sdl2,
  SysUtils;

type

  TScreenMain = class(TMenu)
  public
    TextDescription:     integer;
    TextDescriptionLong: integer;

    // pictures of the entries (theme) and their fade-in on a change
    Preview:      array[0..7] of array of integer;
    PreviewX, PreviewY, PreviewAlpha: array[0..7] of array of real;
    PreviewW, PreviewH: array[0..7] of array of real;
    DescY, DescLongY: real;
    ChangeTicks:  cardinal;
    procedure AnimatePreview;

    constructor Create; override;
    function ParseInput(PressedKey: Cardinal; CharCode: UCS4Char;
      PressedDown: boolean): boolean; override;
    function ParseMouse(MouseButton: integer; BtnDown: boolean; X, Y: integer): boolean; override;
    procedure OnShow; override;
    procedure SetInteraction(Num: integer); override;
    function Draw: boolean; override;
  end;

const
  ID = 'ID_001';   //for help system

var
  WantSoftwareRenderingMsg: boolean;

implementation

uses
  Math,
  UGraphic,
  UHelp,
  UIni,
  ULanguage,
  ULog,
  UNote,
  UParty,
  URenderer,
  USkins,
  USongs,
  UUnicodeUtils;

function TScreenMain.ParseInput(PressedKey: Cardinal; CharCode: UCS4Char;
  PressedDown: boolean): boolean;
begin
  Result := true;

  if (PressedDown) then
  begin // Key Down
        // check normal keys
    case PressedKey of
      SDLK_S: begin
        FadeTo(@ScreenName, SoundLib.Start);
        Exit;
      end;

      SDLK_P: begin
        if (Ini.Players >= 1) and (Party.ModesAvailable) then
        begin
          FadeTo(@ScreenPartyOptions, SoundLib.Start);
          Exit;
        end;
      end;

      SDLK_J: begin
        FadeTo(@ScreenJukeboxPlaylist, SoundLib.Start);
        Exit;
      end;

      SDLK_R: begin
        UGraphic.UnLoadScreens();
        Theme.LoadTheme(Ini.Theme, Ini.Color);
        UGraphic.LoadScreens(USDXVersionStr);
      end;

      SDLK_T: begin
        FadeTo(@ScreenStatMain, SoundLib.Start);
        Exit;
      end;

      SDLK_E: begin
        FadeTo(@ScreenEdit, SoundLib.Start);
        Exit;
      end;

      SDLK_O: begin
        FadeTo(@ScreenOptions, SoundLib.Start);
        Exit;
      end;

      SDLK_A: begin
        FadeTo(@ScreenAbout, SoundLib.Start);
        Exit;
      end;

      SDLK_C: begin
        ScreenAbout.ShowCreditsInAbout;
        FadeTo(@ScreenAbout, SoundLib.Start);
        Exit;
      end;

      SDLK_Q: begin
        Result := false;
        Exit;
      end;
    end;

    // check special keys
    case PressedKey of
      SDLK_ESCAPE,
      SDLK_BACKSPACE:
      begin
        Result := false;
      end;

      SDLK_TAB:
      begin
        ScreenPopupHelp.ShowPopup();
      end;

      SDLK_RETURN:
      begin
        // reset
        Party.bPartyGame := false;

        //Solo
        if (Interaction = 0) then
        begin
          if (Songs.SongList.Count >= 1) then
          begin
            if (Ini.Players >= 0) and (Ini.Players <= 3) then
              PlayersPlay := Ini.Players + 1;
            if (Ini.Players = 4) then
              PlayersPlay := 6;

            if Ini.OnSongClick = sSelectPlayer then
              FadeTo(@ScreenSong)
            else
            begin
              ScreenName.Goto_SingScreen := false;
              FadeTo(@ScreenName, SoundLib.Start);
            end;
          end
          else //show error message
            ScreenPopupError.ShowPopup(Language.Translate('ERROR_NO_SONGS'));
        end;

        //Party
        if Interaction = 1 then
        begin
          if (Songs.SongList.Count >= 1) then
          begin
            Party.bPartyGame := true;

            FadeTo(@ScreenPartyOptions, SoundLib.Start);
          end
          else //show error message, No Songs Loaded
            ScreenPopupError.ShowPopup(Language.Translate('ERROR_NO_SONGS'));
        end;

        //Jukebox
        if Interaction = 2 then
        begin
          if (Songs.SongList.Count >= 1) then
          begin
            FadeTo(@ScreenJukeboxPlaylist, SoundLib.Start);
          end
          else //show error message, No Songs Loaded
            ScreenPopupError.ShowPopup(Language.Translate('ERROR_NO_SONGS'));
        end;

        //Stats
        if Interaction = 3 then
        begin
          FadeTo(@ScreenStatMain, SoundLib.Start);
        end;

        //Editor
        if Interaction = 4 then
        begin
          {$IFDEF UseMIDIPort}
          FadeTo(@ScreenEdit, SoundLib.Start);
          {$ELSE}
          ScreenPopupError.ShowPopup(Language.Translate('ERROR_NO_EDITOR'));
          {$ENDIF}
        end;

        //Options
        if Interaction = 5 then
        begin
          FadeTo(@ScreenOptions, SoundLib.Start);
        end;

        //About
        if Interaction = 6 then
        begin
          FadeTo(@ScreenAbout, SoundLib.Start);
        end;

        //Exit
        if Interaction = 7 then
        begin
          Result := false;
        end;
      end;
      {**
       * Up and Down could be done at the same time,
       * but I don't want to declare variables inside
       * functions like this one, called so many times
       *}
      SDLK_DOWN: InteractInc;
      SDLK_UP: InteractDec;
      SDLK_RIGHT: InteractNext;
      SDLK_LEFT: InteractPrev;
    end;
  end
  else // Key Up
    case PressedKey of
      SDLK_RETURN:
      begin
      end;
    end;
end;

function TScreenMain.ParseMouse(MouseButton: integer; BtnDown: boolean; X, Y: integer): boolean;
begin
  // default mouse behaviour
  Result := inherited ParseMouse(MouseButton, BtnDown, X, Y);
end;

constructor TScreenMain.Create;
var
  I, J: integer;
begin
  inherited Create;
{**
 * Attention ^^:
 * New Creation Order needed because of LoadFromTheme
 * and Button Collections.
 * At First Custom Texts and Statics
 * Then LoadFromTheme
 * after LoadFromTheme the Buttons and Selects
 *}
  TextDescription     := AddText(Theme.Main.TextDescription);
  TextDescriptionLong := AddText(Theme.Main.TextDescriptionLong);

  LoadFromTheme(Theme.Main);

  for I := 0 to 7 do
  begin
    SetLength(Preview[I], Length(Theme.Main.Preview[I]));
    SetLength(PreviewX[I], Length(Theme.Main.Preview[I]));
    SetLength(PreviewY[I], Length(Theme.Main.Preview[I]));
    SetLength(PreviewAlpha[I], Length(Theme.Main.Preview[I]));
    SetLength(PreviewW[I], Length(Theme.Main.Preview[I]));
    SetLength(PreviewH[I], Length(Theme.Main.Preview[I]));
    for J := 0 to High(Theme.Main.Preview[I]) do
    begin
      Preview[I][J] := AddStatic(Theme.Main.Preview[I][J]);
      PreviewX[I][J] := Statics[Preview[I][J]].Texture.X;
      PreviewY[I][J] := Statics[Preview[I][J]].Texture.Y;
      PreviewAlpha[I][J] := Statics[Preview[I][J]].Texture.Alpha;
      PreviewW[I][J] := Statics[Preview[I][J]].Texture.W;
      PreviewH[I][J] := Statics[Preview[I][J]].Texture.H;
      Statics[Preview[I][J]].Visible := false;
    end;
  end;
  DescY := Text[TextDescription].Y;
  DescLongY := Text[TextDescriptionLong].Y;
  ChangeTicks := 0;

  AddButton(Theme.Main.ButtonSolo);
  AddButton(Theme.Main.ButtonMulti);
  AddButton(Theme.Main.ButtonJukebox);
  AddButton(Theme.Main.ButtonStat);
  AddButton(Theme.Main.ButtonEditor);
  AddButton(Theme.Main.ButtonOptions);
  AddButton(Theme.Main.ButtonAbout);
  AddButton(Theme.Main.ButtonExit);

  Interaction := 0;

  WantSoftwareRenderingMsg := Renderer.SoftwareRendering;
end;

procedure TScreenMain.OnShow;
begin
  inherited;

  SoundLib.StartBgMusic;

  ScreenSong.Mode := smNormal;

  if not Help.SetHelpID(ID) then
    Log.LogWarn('No Entry for Help-ID ' + ID, 'ScreenMains');

 {**
  * Clean up TPartyGame here
  * at the moment there is no better place for this
  *}
  Party.Clear;
end;

{ the picture and the description of the selected entry come in with a short
  fade and slide }
procedure TScreenMain.AnimatePreview;
var
  I, J: integer;
  T, E, V, S, NX, NY, NW, NH: real;
  Now: cardinal;
begin
  Now := SDL_GetTicks();
  if (ChangeTicks = 0) then
    T := 1
  else
    T := (SDL_GetTicks() - ChangeTicks) / 320;
  if (T > 1) then
    T := 1;
  E := 1 - (1 - T) * (1 - T) * (1 - T);
  for I := 0 to 7 do
    for J := 0 to High(Preview[I]) do
    begin
      Statics[Preview[I][J]].Visible := (I = Interaction);
      if (I = Interaction) then
      begin
        // the pieces arrive one after the other
        T := (SDL_GetTicks() - ChangeTicks - J * 18) / 320;
        if (ChangeTicks = 0) or (T > 1) then
          T := 1
        else if (T < 0) then
          T := 0;
        T := 1 - (1 - T) * (1 - T) * (1 - T);
        // then they keep moving a little while the entry stays selected
        with Theme.Main.Preview[I][J] do
        begin
          V := 0;
          if (IdlePeriod > 0) then
          begin
            V := Frac(Now / IdlePeriod + IdlePhase);
            if (IdleWave = 1) then
            begin
              // 0 -> 1 -> 0, resting a moment at both ends
              V := 1 - Abs(2 * V - 1);
              V := V * V * (3 - 2 * V);
            end
            else
              V := Sin(2 * Pi * V);
          end;
          // the motion grows in after the arrival
          V := V * T;
          NW := PreviewW[I][J] + IdleDW * V;
          NH := PreviewH[I][J] + IdleDH * V;
          NX := PreviewX[I][J] + (1 - T) * 24 + IdleDX * V;
          NY := PreviewY[I][J] + IdleDY * V - IdleDH * V;
          S := 1 + IdleScale * V;
          Statics[Preview[I][J]].Texture.W := NW * S;
          Statics[Preview[I][J]].Texture.H := NH * S;
          Statics[Preview[I][J]].Texture.X := NX - NW * (S - 1) / 2;
          Statics[Preview[I][J]].Texture.Y := NY - NH * (S - 1) / 2;
          Statics[Preview[I][J]].Texture.Rot := IdleRot * V * Pi / 180;
          if (IdleWave = 1) then
            Statics[Preview[I][J]].Texture.Alpha := PreviewAlpha[I][J] * T * (1 - IdleAlpha * V)
          else
            Statics[Preview[I][J]].Texture.Alpha := PreviewAlpha[I][J] * T * (1 - IdleAlpha * (V / Max(T, 0.001) + 1) / 2);
        end;
      end;
    end;
  Text[TextDescription].Alpha := E;
  Text[TextDescription].Y := DescY + (1 - E) * 10;
  Text[TextDescriptionLong].Alpha := E;
  Text[TextDescriptionLong].Y := DescLongY + (1 - E) * 10;
end;

function TScreenMain.Draw: boolean;
begin
  AnimatePreview;
  Result := inherited Draw;

  if not ScreenPopupError.Visible then
  begin
    if WantSoftwareRenderingMsg then
    begin
      WantSoftwareRenderingMsg := false;
      ScreenPopupError.ShowPopup(Language.Translate('ERROR_SOFTWARE_RENDERING'));
    end;
  end;
end;

procedure TScreenMain.SetInteraction(Num: integer);
begin
  if (Num <> Interaction) then
    ChangeTicks := SDL_GetTicks();
  inherited SetInteraction(Num);
  Text[TextDescription].Text     := Theme.Main.Description[Interaction];
  Text[TextDescriptionLong].Text := Theme.Main.DescriptionLong[Interaction];
end;

end.
