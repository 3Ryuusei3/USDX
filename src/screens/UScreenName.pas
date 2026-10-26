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
 * $URL: https://ultrastardx.svn.sourceforge.net/svnroot/ultrastardx/trunk/src/screens/UScreenName.pas $
 * $Id: UScreenName.pas 1939 2009-11-09 00:27:55Z s_alexander $
 *}

unit UScreenName;

interface

{$IFDEF FPC}
  {$MODE Delphi}
{$ENDIF}

{$I switches.inc}

uses
  UAvatars,
  UDisplay,
  UFiles,
  UIni,
  UMenu,
  UMusic,
  UNote,
  UScreenScore,
  UScreenSingController,
  UScreenHighScores,
  UThemes,
  SysUtils,
  sdl2,
  md5;

type
  TScreenName = class(TMenu)
    private
      PlayersCount:  cardinal;
      PlayerAvatar:  cardinal;
      PlayerName:    cardinal;
      PlayerColor:   cardinal;
      PlayerSelect:  cardinal;
      PlayerSelectLevel: cardinal;

      CountIndex:   integer;
      PlayerIndex:  integer;
      ColorIndex:   integer;
      LevelIndex:   integer;

      PlayerAvatarIID: integer; // interaction ID

      AvatarCurrent: real;
      AvatarTarget:  integer;

      NumVisibleAvatars:      integer;
      DistanceVisibleAvatars: integer;

      isScrolling: boolean;   // true if avatar flow is about to move

      PlayerCurrent:       array [0..UIni.IMaxPlayerCount-1] of integer;
      PlayerCurrentText:   array [0..UIni.IMaxPlayerCount-1] of integer;
      PlayerCurrentAvatar: array [0..UIni.IMaxPlayerCount-1] of integer;

      PlayerNames:   array [0..UIni.IMaxPlayerCount-1] of UTF8String;
      PlayerAvatars: array [0..UIni.IMaxPlayerCount-1] of integer;
      PlayerLevel:   array [0..UIni.IMaxPlayerCount-1] of integer;

      APlayerColor: array of integer;

      PlayerAvatarButton: array of integer;

      // card layout (theme NameCards)
      CardsOpened: cardinal;          // for the cards' entrance
      CardFocusTicks: cardinal;       // last change of the edited player
      LastPlayerIndex: integer;
      CardAnimX, CardAnimY, CardAnimW, CardAnimH: real; // ring position (eased)
      procedure DrawCards;
      procedure SwitchPlayer(Index: integer);
      function MicLabel(Player: integer): UTF8String;

    public
      Goto_SingScreen: boolean; //If true then next Screen in SingScreen
      
      constructor Create; override;
      function ShouldHandleInput(PressedKey: cardinal; CharCode: UCS4Char; PressedDown: boolean; out SuppressKey: boolean): boolean; override;
      function ParseInput(PressedKey: cardinal; CharCode: UCS4Char; PressedDown: boolean): boolean; override;
      function ParseMouse(MouseButton: integer; BtnDown: boolean; X, Y: integer): boolean; override;

      procedure OnShow; override;
      function Draw: boolean; override;

      procedure SetAvatarScroll;
      procedure SelectNext;
      procedure SelectPrev;

      procedure PlayerColorButton(K: integer);
      function NoRepeatColors(ColorP: integer; Interaction: integer; Pos: integer):integer;
      procedure RefreshPlayers();
      procedure RefreshProfile();
      procedure RefreshColor();

      procedure ChangeSelectPlayerPosition(Player: integer);

      procedure GenerateAvatars();
      procedure SetPlayerAvatar(Player: integer);
  end;

var
  Num: array[0..UIni.IMaxPlayerCount-1]of integer;

const
  ID='ID_010';   //for help system

implementation

uses

  UCommon,
  UText,
  UGraphic,
  UHelp,
  ULanguage,
  ULog,
  UMain,
  UMenuButton,
  UPath,
  URenderer,
  USkins,
  USongs,
  UTime,
  UUnicodeUtils,
  Math;

function TScreenName.ParseMouse(MouseButton: integer; BtnDown: boolean; X, Y: integer): boolean;
var
  I: integer;
  Btn: integer;
begin
  Result := true;

  inherited ParseMouse(MouseButton, BtnDown, X, Y);
  SetTextInput(Button[PlayerName].Selected);

  // transfer mousecords to the 800x600 raster we use to draw
  X := Round((X / (ScreenW / Screens)) * RenderW);
  if (X > RenderW) then
    X := X - RenderW;
  Y := Round((Y / ScreenH) * RenderH);

  if (BtnDown) then
  begin
     //if RightMbESC is set, send ESC keypress
    if RightMbESC and (MouseButton = SDL_BUTTON_RIGHT) then
      Result:=ParseInput(SDLK_ESCAPE, 0, true);

    //scrolling avatars with mousewheel
    if (MouseButton = SDL_BUTTON_WHEELDOWN) then
    begin
      if (Interaction = PlayerAvatarIID) then
        ParseInput(SDLK_RIGHT, 0, true);
    end
    else if (MouseButton = SDL_BUTTON_WHEELUP) then
    begin
      if (Interaction = PlayerAvatarIID) then
        ParseInput(SDLK_LEFT, 0, true);
    end
    else
    begin
      // click avatars
      // 1st left
      Btn := AvatarTarget - 2;
      if (Btn < 0) then
        Btn := High(AvatarsList);

      if InRegion(X, Y, Button[PlayerAvatarButton[Btn]].GetMouseOverArea) then
      begin
        Interaction := 2;

        ParseInput(SDLK_LEFT, 0, true);
        ParseInput(SDLK_LEFT, 0, true);
      end;

      // 2nd left
      Btn := AvatarTarget - 1;
      if (Btn < 0) then
        Btn := High(AvatarsList);

      if InRegion(X, Y, Button[PlayerAvatarButton[Btn]].GetMouseOverArea) then
      begin
        Interaction := 2;

        ParseInput(SDLK_LEFT, 0, true);
      end;

      // 1st right
      Btn := AvatarTarget + 1;
      if (Btn > High(AvatarsList)) then
        Btn := 0;

      if InRegion(X, Y, Button[PlayerAvatarButton[Btn]].GetMouseOverArea) then
      begin
        Interaction := 2;

        ParseInput(SDLK_RIGHT, 0, true);
      end;

      // 2nd right
      Btn := AvatarTarget + 2;
      if (Btn > High(AvatarsList)) then
        Btn := 0;

      if InRegion(X, Y, Button[PlayerAvatarButton[Btn]].GetMouseOverArea) then
      begin
        Interaction := 2;

        ParseInput(SDLK_RIGHT, 0, true);
        ParseInput(SDLK_RIGHT, 0, true);
      end;

      // click for change player profile
      for I := 0 to 5 do
      begin
        if Statics[PlayerCurrent[I]].Visible and InRegion(X, Y, Statics[PlayerCurrent[I]].GetMouseOverArea) then
        begin
          PlayerIndex := I;

          RefreshProfile();

          isScrolling := true;
          AvatarTarget := PlayerAvatars[PlayerIndex];
        end;
      end;
    end;
  end;
end;

function TScreenName.ShouldHandleInput(PressedKey: cardinal; CharCode: UCS4Char; PressedDown: boolean; out SuppressKey: boolean): boolean;
begin
  Result := inherited;
  // only suppress special keys for now
  case PressedKey of
    // Templates for Names Mod
    SDLK_F1, SDLK_F2, SDLK_F3, SDLK_F4, SDLK_F5, SDLK_F6, SDLK_F7, SDLK_F8, SDLK_F9, SDLK_F10, SDLK_F11, SDLK_F12:
     if (Button[PlayerName].Selected) then
     begin
       SuppressKey := true;
     end
     else
     begin
       Result := false;
     end;
  end;
end;

function TScreenName.ParseInput(PressedKey: cardinal; CharCode: UCS4Char; PressedDown: boolean): boolean;
  var
    I: integer;
    SDL_ModState: word;
    Col: TRGB;

  procedure HandleNameTemplate(const index: integer);
  var
    isAlternate: boolean;
  begin
    isAlternate := (SDL_ModState = KMOD_LSHIFT) or (SDL_ModState = KMOD_RSHIFT);
    isAlternate := isAlternate or (SDL_ModState = KMOD_LALT); // legacy key combination

    if isAlternate then
    begin
      Ini.NameTemplate[index] := Button[PlayerName].Text[0].Text;
    end
    else
    begin
      Button[PlayerName].Text[0].Text := Ini.NameTemplate[index];
      PlayerNames[PlayerIndex] := Button[PlayerName].Text[0].Text;
    end;
  end;

begin
  Result := true;
  if (PressedDown) then
  begin // Key Down

    SDL_ModState := SDL_GetModState and (KMOD_LSHIFT + KMOD_RSHIFT
    + KMOD_LCTRL + KMOD_RCTRL + KMOD_LALT  + KMOD_RALT);

    if (not Button[PlayerName].Selected) then
    begin
      // check normal keys
      case PressedKey of
        SDLK_Q:
          begin
            Result := false;
            Exit;
          end;
      end;
    end
    else if (Interaction = 3) and (IsPrintableChar(CharCode)) then
    begin
      // pass printable chars to button
      Button[PlayerName].Text[0].Text := Button[PlayerName].Text[0].Text +
                                          UCS4ToUTF8String(CharCode);

      PlayerNames[PlayerIndex] := Button[PlayerName].Text[0].Text;
      Exit;
    end;

    // check special keys
    case PressedKey of

      // Templates for Names Mod
      SDLK_F1: HandleNameTemplate(0);
      SDLK_F2: HandleNameTemplate(1);
      SDLK_F3: HandleNameTemplate(2);
      SDLK_F4: HandleNameTemplate(3);
      SDLK_F5: HandleNameTemplate(4);
      SDLK_F6: HandleNameTemplate(5);
      SDLK_F7: HandleNameTemplate(6);
      SDLK_F8: HandleNameTemplate(7);
      SDLK_F9: HandleNameTemplate(8);
      SDLK_F10: HandleNameTemplate(9);
      SDLK_F11: HandleNameTemplate(10);
      SDLK_F12: HandleNameTemplate(11);

      SDLK_BACKSPACE:
        begin
          if (Interaction = 3) then
          begin
            Button[PlayerName].Text[0].DeleteLastLetter();
            PlayerNames[PlayerIndex] := Button[PlayerName].Text[0].Text;
          end
          else
            ParseInput(SDLK_ESCAPE, CharCode, PressedDown);
        end;

      SDLK_TAB:
        begin
          ScreenPopupHelp.ShowPopup();
        end;

      SDLK_ESCAPE :
        begin
          StopTextInput;
          Ini.SaveNames;
          AudioPlayback.PlaySound(SoundLib.Back);
          if GoTo_SingScreen then
            FadeTo(@ScreenSong)
          else
            FadeTo(@ScreenMain);
        end;

      SDLK_RETURN:
        begin
          StopTextInput;
          Ini.Players := CountIndex;
          PlayersPlay:= UIni.IPlayersVals[CountIndex];
          SetLength(Player, PlayersPlay);

          for I := 1 to PlayersPlay do
          begin
            // TODO: is it really necessary for this screen to duplicate all these Ini. arrays?
            Ini.Name[I-1] := PlayerNames[I-1];
            Ini.PlayerColor[I-1] := Num[I-1];
            Ini.SingColor[I-1] := Num[I-1];
            Ini.PlayerLevel[I-1] := PlayerLevel[I-1];
            // also set (some) of this info in the much easier to use Player variable
            Player[I-1].Name := PlayerNames[I-1];
            Player[I-1].Level := PlayerLevel[I-1];

            Ini.PlayerAvatar[I-1] := AvatarsMD5[PlayerAvatars[I-1]];

            if (PlayerAvatars[I-1] = 0) then
            begin
              AvatarPlayerTextures[I] := NoAvatartexture[I];

              Col := GetPlayerColor(Num[I-1]);

              AvatarPlayerTextures[I].ColR := Col.R;
              AvatarPlayerTextures[I].ColG := Col.G;
              AvatarPlayerTextures[I].ColB := Col.B;
            end
            else
            begin
              Button[PlayerAvatarButton[PlayerAvatars[I-1]]].Texture.Int := 1;
              AvatarPlayerTextures[I] := Button[PlayerAvatarButton[PlayerAvatars[I-1]]].Texture.Clone();
            end;

          end;

          Ini.SaveNumberOfPlayers;
          Ini.SaveNames;
          Ini.SavePlayerColors;
          Ini.SavePlayerAvatars;
          Ini.SavePlayerLevels;

          LoadPlayersColors;
          Theme.ThemeScoreLoad;

          // Reload ScreenSing and ScreenScore because of player colors
          // TODO: do this better  REALLY NECESSARY?
          ScreenScore.Free;
          ScreenSing.Free;

          ScreenScore := TScreenScore.Create;
          ScreenSing  := TScreenSingController.Create;
          //

          AudioPlayback.PlaySound(SoundLib.Start);

          if GoTo_SingScreen then
          begin
            // if we've been in the player screen, we need to show the warning again
            ScreenSing.CheckPlayerConfigOnNextSong := true;
            FadeTo(@ScreenSing);
            GoTo_SingScreen := false;
          end
          else
          begin
            FadeTo(@ScreenSong);
            GoTo_SingScreen := false;
          end;
        end;

      // Up and Down could be done at the same time,
      // but I don't want to declare variables inside
      // functions like this one, called so many times
      SDLK_DOWN:
      begin
        if Theme.Name.Cards.Enabled then
        begin
          // cards: after the difficulty comes the next player's name;
          // nothing wraps around to the top
          if (Interaction = 5) then
          begin
            if (PlayerIndex < UIni.IPlayersVals[CountIndex] - 1) then
            begin
              SwitchPlayer(PlayerIndex + 1);
              Interaction := 3;
            end;
          end
          else
            InteractNext;
        end
        else
          InteractNext;
        SetTextInput(Button[PlayerName].Selected);
      end;

      SDLK_UP:
      begin
        if Theme.Name.Cards.Enabled then
        begin
          if (Interaction = 3) and (PlayerIndex > 0) then
          begin
            SwitchPlayer(PlayerIndex - 1);
            Interaction := 5;
          end
          else if (Interaction > 0) then
            InteractPrev;
        end
        else
          InteractPrev;
        SetTextInput(Button[PlayerName].Selected);
      end;

      SDLK_RIGHT:
        begin
          AudioPlayback.PlaySound(SoundLib.Change);

          if Theme.Name.Cards.Enabled and (Interaction = 3) then
          begin
            if (PlayerIndex < UIni.IPlayersVals[CountIndex] - 1) then
              SwitchPlayer(PlayerIndex + 1);
            Exit;
          end;

          if (Interaction in [0, 4, 5]) then
            InteractInc;

          if (Interaction = 0) then
            RefreshPlayers();

          if (Interaction = 1) then
          begin //TODO: adapt this to new playersize
              if (PlayerIndex < UIni.IPlayersVals[CountIndex]-1) then
            begin
              PlayerIndex := PlayerIndex + 1;

              RefreshProfile();

              isScrolling := true;
              AvatarTarget := PlayerAvatars[PlayerIndex];
            end;
          end;

          if (Interaction = 2) then
          begin
            SelectNext;
            SetAvatarScroll;
            PlayerAvatars[PlayerIndex] := AvatarTarget;
            SetPlayerAvatar(PlayerIndex);
          end;

          if (Interaction = 4) then
          begin
            RefreshColor();
            SelectsS[PlayerColor].SetSelect(true);
          end;

          if (Interaction = 5) then
          begin
            PlayerLevel[PlayerIndex] := LevelIndex;
          end;

        end;
      SDLK_LEFT:
        begin
          AudioPlayback.PlaySound(SoundLib.Change);

          if Theme.Name.Cards.Enabled and (Interaction = 3) then
          begin
            if (PlayerIndex > 0) then
              SwitchPlayer(PlayerIndex - 1);
            Exit;
          end;

          if (Interaction in [0, 4, 5]) then
            InteractDec;

          if (Interaction = 0) then
            RefreshPlayers();

          if (Interaction = 1) then
          begin
            if (PlayerIndex > 0) then
            begin
              PlayerIndex := PlayerIndex - 1;

              RefreshProfile();

              isScrolling := true;
              AvatarTarget := PlayerAvatars[PlayerIndex];
            end;
          end;

          if (Interaction = 2) then
          begin
            SelectPrev;
            SetAvatarScroll;
            PlayerAvatars[PlayerIndex] := AvatarTarget;
            SetPlayerAvatar(PlayerIndex);
          end;

          if (Interaction = 4) then
          begin
            RefreshColor();
            SelectsS[PlayerColor].SetSelect(true);
          end;

          if (Interaction = 5) then
          begin
            PlayerLevel[PlayerIndex] := LevelIndex;
          end;
        end;

    end;
  end;
end;

procedure TScreenName.GenerateAvatars();
var
  I: integer;
  Avatar: TAvatar;
begin

  SetLength(PlayerAvatarButton, Length(AvatarsList) + 1);

  // 1st no-avatar dummy
  for I := 1 to UIni.IMaxPlayerCount do
  begin
    NoAvatarTexture[I] := Renderer.GetTexture(Skin.GetTextureFileName('NoAvatar_P' + IntToStr(I)), TEXTURE_TYPE_TRANSPARENT, $FFFFFF);
  end;

  // create no-avatar
  PlayerAvatarButton[0] := AddButton(Theme.Name.PlayerAvatar);
  Button[PlayerAvatarButton[0]].Texture.Free;
  Button[PlayerAvatarButton[0]].Texture := NoAvatarTexture[1].Clone;
  Button[PlayerAvatarButton[0]].Selectable := false;
  Button[PlayerAvatarButton[0]].Selected := false;
  Button[PlayerAvatarButton[0]].Visible := false;

  // create avatars buttons
  for I := 1 to High(AvatarsList) do
  begin
    // create avatar
    PlayerAvatarButton[I] := AddButton(Theme.Name.PlayerAvatar);

    // load avatar directly from its file
    Avatar := Avatars.AddAvatar(AvatarsList[I]);

    if (Avatar <> nil) then
    begin
      Button[PlayerAvatarButton[I]].Texture.Free;
      Button[PlayerAvatarButton[I]].Texture := Avatar.GetTexture();
      Button[PlayerAvatarButton[I]].Selectable := false;
      Button[PlayerAvatarButton[I]].Selected := false;
      Button[PlayerAvatarButton[I]].Visible := false;
    end;

    Avatar.Free;
  end;

end;

procedure TScreenName.SwitchPlayer(Index: integer);
begin
  PlayerIndex := Index;
  RefreshProfile();
  isScrolling := true;
  AvatarTarget := PlayerAvatars[PlayerIndex];
end;

{ "Mic 1" / "Mic 1 · canal 2" for the microphone a player sings into }
function TScreenName.MicLabel(Player: integer): UTF8String;
var
  D, C: integer;
begin
  Result := '';
  for D := 0 to High(Ini.InputDeviceConfig) do
    for C := 0 to High(Ini.InputDeviceConfig[D].ChannelToPlayerMap) do
      if (Ini.InputDeviceConfig[D].ChannelToPlayerMap[C] = Player + 1) then
      begin
        Result := 'Mic ' + IntToStr(D + 1);
        if (Length(Ini.InputDeviceConfig[D].ChannelToPlayerMap) > 1) then
          Result := Result + ' ' + UTF8Encode(WideString(WideChar($00B7))) + ' ' +
                    Language.Translate('NAME_CARD_CHANNEL') + ' ' + IntToStr(C + 1);
        Exit;
      end;
end;

{ one card per player: colour, name, microphone, colour and difficulty. The
  edited player's card holds the real name field and colour slide; the
  difficulty is shown as three segments (the slide itself is hidden) }
procedure TScreenName.DrawCards;
const
  ANIM_MS = 220;
var
  Count, Rows, I, Col, Row, S: integer;
  CW, CH, CX, CY, SegW, T, E, X, Y, W, H: real;
  Tex: TTexture;
  Ring, Circle, Card, Seg, Track: TTexture;
  R, G, B: real;
  PCol: TRGB;
  Name, Initial, Lbl: UTF8String;
  CirS, CirX, CirY, TxX, LblY, NameY, ColY: real;
  NameSize: integer;
  Now: cardinal;

  procedure Pal(const ColorName: string; out PR, PG, PB: real);
  begin
    PR := 1; PG := 1; PB := 1;
    LoadColor(PR, PG, PB, ColorName);
  end;

  procedure Put(Tex: TTexture; PX, PY, PW, PH, PR, PG, PB, PA: real);
  begin
    if (Tex = nil) then
      Exit;
    Tex.X := PX; Tex.Y := PY; Tex.W := PW; Tex.H := PH; Tex.Z := 0.5;
    Tex.ColR := PR; Tex.ColG := PG; Tex.ColB := PB; Tex.Alpha := PA;
    Tex.TexX1 := 0; Tex.TexY1 := 0; Tex.TexX2 := 1; Tex.TexY2 := 1;
    Renderer.DrawTexture(Tex);
  end;

  procedure Txt(const S: UTF8String; PX, PY: real; Size: integer; Font, Style: integer; const ColorName: string;
                PA: real; Align: integer = 0);
  var
    TR, TG, TB, TW: real;
  begin
    Pal(ColorName, TR, TG, TB);
    SetFontFamily(Font);
    SetFontStyle(Style);
    SetFontItalic(false);
    SetFontSize(Size);
    SetFontReflection(false, 0);
    TW := TextWidth(S);
    if (Align = 1) then
      PX := PX - TW / 2;
    SetFontPos(PX, PY);
    SetFontColor(TR, TG, TB, PA);
    PrintText(S);
  end;

begin
  with Theme.Name.Cards do
  begin
    Card := Renderer.GetTexture(Skin.GetTextureFileName(CardTex), TEXTURE_TYPE_TRANSPARENT);
    Ring := Renderer.GetTexture(Skin.GetTextureFileName(RingTex), TEXTURE_TYPE_TRANSPARENT);
    Circle := Renderer.GetTexture(Skin.GetTextureFileName(CircleTex), TEXTURE_TYPE_TRANSPARENT);
    Seg := Renderer.GetTexture(Skin.GetTextureFileName(SegTex), TEXTURE_TYPE_TRANSPARENT);
    Track := Renderer.GetTexture(Skin.GetTextureFileName(TrackTex), TEXTURE_TYPE_TRANSPARENT);

    Now := SDL_GetTicks();
    if (CardsOpened = 0) then
      CardsOpened := Now;

    Count := UIni.IPlayersVals[CountIndex];
    Rows := (Count + Cols - 1) div Cols;
    CW := (W - Gap * (Cols - 1)) / Cols;
    CH := (H - Gap * (Rows - 1)) / Rows;
    if (CH > MaxH) then
      CH := MaxH;

    for I := 0 to Count - 1 do
    begin
      Col := I mod Cols;
      Row := I div Cols;
      CX := X + Col * (CW + Gap);
      CY := Y + Row * (CH + Gap);

      // entrance: the cards rise in one after the other
      T := (Now - CardsOpened - I * 45) / ANIM_MS;
      if (T < 0) then T := 0 else if (T > 1) then T := 1;
      E := 1 - (1 - T) * (1 - T) * (1 - T);
      CY := CY + (1 - E) * 18;

      if (I = PlayerIndex) then
        Pal('Surface2', R, G, B)
      else
        Pal('Surface', R, G, B);
      Put(Card, CX, CY, CW, CH, R, G, B, E);

      PCol := GetPlayerColor(Num[I]);
      if (I = PlayerIndex) then
      begin
        // the edited card: ring follows it smoothly
        if (LastPlayerIndex <> PlayerIndex) or (CardAnimW = 0) then
        begin
          if (CardAnimW = 0) then
          begin
            CardAnimX := CX; CardAnimY := CY; CardAnimW := CW; CardAnimH := CH;
          end;
          LastPlayerIndex := PlayerIndex;
          CardFocusTicks := Now;
        end;
        T := (Now - CardFocusTicks) / ANIM_MS;
        if (T > 1) then T := 1;
        CardAnimX := CardAnimX + (CX - CardAnimX) * T;
        CardAnimY := CardAnimY + (CY - CardAnimY) * T;
        CardAnimW := CardAnimW + (CW - CardAnimW) * T;
        CardAnimH := CardAnimH + (CH - CardAnimH) * T;
      end;

      // compact cards (two rows of players) put everything closer
      if (CH < 230) then
      begin
        CirS := 44; CirX := 20; CirY := 18; TxX := 76; LblY := 18; NameY := 32; NameSize := 20;
        ColY := 74;
      end
      else
      begin
        CirS := 56; CirX := 24; CirY := 24; TxX := 96; LblY := 26; NameY := 46; NameSize := 24;
        ColY := CH - 112;
      end;

      // colour circle with the initial
      Put(Circle, CX + CirX, CY + CirY, CirS, CirS, PCol.R, PCol.G, PCol.B, E);
      if (I = PlayerIndex) then
        Name := Button[PlayerName].Text[0].Text
      else
        Name := PlayerNames[I];
      Initial := UTF8UpperCase(UTF8Copy(Trim(Name), 1, 1));
      Txt(Initial, CX + CirX + CirS / 2, CY + CirY + CirS / 2 - CirS * 0.24, Round(CirS * 0.46), TitleFont, 1,
          'OnAccent', E, 1);

      Lbl := UTF8UpperCase(Language.Translate('NAME_CARD_PLAYER')) + ' ' + IntToStr(I + 1);
      if (MicLabel(I) <> '') then
        Lbl := Lbl + '  ' + UTF8Encode(WideString(WideChar($00B7))) + '  ' + MicLabel(I);
      Txt(Lbl, CX + TxX, CY + LblY, 12, Font, 1, 'Text3', E);
      if (I <> PlayerIndex) then
        Txt(Name, CX + TxX, CY + NameY, NameSize, TitleFont, 0, 'Text', E);

      // colour (the edited card has the slide there)
      if (I <> PlayerIndex) then
      begin
        Txt('Color', CX + 24, CY + ColY + 12, 15, Font, 0, 'Text3', E);
        Put(Circle, CX + 114, CY + ColY + 14, 14, 14, PCol.R, PCol.G, PCol.B, E);
        Txt(IPlayerColorTranslated[Num[I] - 1], CX + 136, CY + ColY + 12, 15, Font, 0, 'Text2', E);
      end;

      // difficulty as three segments
      SegW := (CW - 48 - 8) / 3;
      Pal('Bg', R, G, B);
      Put(Track, CX + 20, CY + CH - 60, CW - 40, 44, R, G, B, E * 0.9);
      for S := 0 to 2 do
      begin
        if (PlayerLevel[I] = S) then
        begin
          if (I = PlayerIndex) and (Interaction = 5) then
            Put(Seg, CX + 24 + S * (SegW + 4), CY + CH - 56, SegW, 36, PCol.R, PCol.G, PCol.B, E)
          else
          begin
            Pal('Line', R, G, B);
            Put(Seg, CX + 24 + S * (SegW + 4), CY + CH - 56, SegW, 36, R, G, B, E);
          end;
        end;
        if (PlayerLevel[I] = S) and (I = PlayerIndex) and (Interaction = 5) then
          Txt(IDifficultyTranslated[S], CX + 24 + S * (SegW + 4) + SegW / 2, CY + CH - 47, 15, Font, 1, 'OnAccent', E, 1)
        else if (PlayerLevel[I] = S) then
          Txt(IDifficultyTranslated[S], CX + 24 + S * (SegW + 4) + SegW / 2, CY + CH - 47, 15, Font, 1, 'Text', E, 1)
        else
          Txt(IDifficultyTranslated[S], CX + 24 + S * (SegW + 4) + SegW / 2, CY + CH - 47, 15, Font, 0, 'Text3', E, 1);
      end;

      // the real widgets of the edited player go into his card
      if (I = PlayerIndex) then
      begin
        Button[PlayerName].X := CX + TxX - 8;
        Button[PlayerName].Y := CY + NameY - 12;
        SelectsS[PlayerColor].SetX(CX + 20);
        SelectsS[PlayerColor].SetY(CY + ColY);
      end;
    end;

    // ring around the edited card: accent while choosing the player
    if (Interaction = 1) then
      Pal('Accent', R, G, B)
    else
      Pal('Line2', R, G, B);
    Put(Ring, CardAnimX - 3, CardAnimY - 3, CardAnimW + 6, CardAnimH + 6, R, G, B, 1);

    // hidden widgets (still used for the keys)
    Button[PlayerSelect].X := -4000;
    SelectsS[PlayerSelectLevel].SetX(-4000);
  end;
end;

procedure TScreenName.ChangeSelectPlayerPosition(Player: integer);
begin
  Button[PlayerSelect].X := Theme.Name.PlayerSelect[Player].X + Theme.Name.PlayerSelectCurrent.X;
end;

procedure TScreenName.RefreshPlayers();
var
  Count, I: integer;
  DesCol: TRGB;
begin

  Count := UIni.IPlayersVals[CountIndex];

  while (PlayerIndex > Count-1) do
    PlayerIndex := PlayerIndex - 1;

  // Player Colors
  for I := Count-1 downto 0 do
  begin
    if (Ini.PlayerColor[I] > 0) then
      Num[I] := NoRepeatColors(Ini.PlayerColor[I], I, 1)
    else
      Num[I] := NoRepeatColors(1, I, 1);

    DesCol := GetPlayerColor(Num[I]);

    Statics[PlayerCurrent[I]].Texture.ColR := DesCol.R;
    Statics[PlayerCurrent[I]].Texture.ColG := DesCol.G;
    Statics[PlayerCurrent[I]].Texture.ColB := DesCol.B;
  end;

  for I := 0 to UIni.IMaxPlayerCount-1 do
  begin
    Statics[PlayerCurrent[I]].Visible := I < Count;
    Text[PlayerCurrentText[I]].Visible := I < Count;
    Statics[PlayerCurrentAvatar[I]].Visible := (I < Count) and Theme.Name.PlayerScrollAvatar.Show;
  end;

  // list players
  for I := 0 to Count -1 do
  begin
    Text[PlayerCurrentText[I]].Text := PlayerNames[I];
    SetPlayerAvatar(I);
  end;

  RefreshProfile();

  AvatarTarget := PlayerAvatars[PlayerIndex];
  AvatarCurrent := AvatarTarget;

end;

procedure TScreenName.RefreshProfile();
var
  ITmp: array of UTF8String;
  Count, Max, I, J, Index: integer;
  Used: boolean;
begin
  // no-avatar for current player
  Button[PlayerAvatarButton[0]].Texture.Free;
  Button[PlayerAvatarButton[0]].Texture := NoAvatarTexture[PlayerIndex + 1].Clone();

  Button[PlayerName].Text[0].Text := PlayerNames[PlayerIndex];

  SelectsS[PlayerSelectLevel].SetSelectOpt(PlayerLevel[PlayerIndex]);

  Count := UIni.IPlayersVals[CountIndex];

  ChangeSelectPlayerPosition(PlayerIndex);

  PlayerColorButton(Num[PlayerIndex]);

  Max := Length(IPlayerColorTranslated) - Count + 1;
  SetLength(ITmp, Max);

  APlayerColor := nil;
  SetLength(APlayerColor, Max);

  Index := 0;
  for I := 0 to High(IPlayerColorTranslated) do      //for every color
  begin
    Used := false;

    for J := 0 to Count -1 do      //for every active player
    begin
      if (Num[J] - 1 = I) and (J <> PlayerIndex) then   //check if color is already used for not current player
      begin
        Used := true;
        break;
      end;
    end;

    if not (Used) then
    begin
      ITmp[Index] := IPlayerColorTranslated[I];
      APlayerColor[Index] := I + 1;
      Index := Index + 1;
    end;
  end;

  UpdateSelectSlideOptions(PlayerColor, ITmp, ColorIndex);

  for I := 0 to High(APlayerColor) do
  begin
    if (Num[PlayerIndex] = APlayerColor[I]) then
    begin
      SelectsS[PlayerColor].SetSelectOpt(I);
      break;
    end;
  end;

end;

procedure TScreenName.RefreshColor();
begin

  PlayerColorButton(APlayerColor[ColorIndex]);

end;

function TScreenName.NoRepeatColors(ColorP:integer; Interaction:integer; Pos:integer):integer;
var
  Z, Count:integer;
begin
  Count := UIni.IPlayersVals[CountIndex];

  if (ColorP > Length(IPlayerColorTranslated)) then
    ColorP := NoRepeatColors(1, Interaction, Pos);

  if (ColorP <= 0) then
    ColorP := NoRepeatColors(High(IPlayerColorTranslated), Interaction, Pos);

  for Z := Count -1 downto 0 do
  begin
    if (Num[Z] = ColorP) and (Z <> Interaction) then
      ColorP := NoRepeatColors(ColorP + Pos, Interaction, Pos)
  end;

  Result := ColorP;

end;

procedure TScreenName.PlayerColorButton(K: integer);
var
  Col, DesCol: TRGB;
begin

  Col := GetPlayerLightColor(K);

  Button[PlayerName].SelectColR:= Col.R;
  Button[PlayerName].SelectColG:= Col.G;
  Button[PlayerName].SelectColB:= Col.B;

  Button[PlayerAvatar].SelectColR:= Col.R;
  Button[PlayerAvatar].SelectColG:= Col.G;
  Button[PlayerAvatar].SelectColB:= Col.B;

  SelectsS[PlayerColor].SBGColR:= Col.R;
  SelectsS[PlayerColor].SBGColG:= Col.G;
  SelectsS[PlayerColor].SBGColB:= Col.B;

  SelectsS[PlayerSelectLevel].SBGColR:= Col.R;
  SelectsS[PlayerSelectLevel].SBGColG:= Col.G;
  SelectsS[PlayerSelectLevel].SBGColB:= Col.B;

  DesCol := GetPlayerColor(K);

  Statics[PlayerCurrent[PlayerIndex]].Texture.ColR := DesCol.R;
  Statics[PlayerCurrent[PlayerIndex]].Texture.ColG := DesCol.G;
  Statics[PlayerCurrent[PlayerIndex]].Texture.ColB := DesCol.B;

  Button[PlayerName].DeselectColR:= DesCol.R;
  Button[PlayerName].DeselectColG:= DesCol.G;
  Button[PlayerName].DeselectColB:= DesCol.B;

  Button[PlayerAvatar].DeselectColR:= DesCol.R;
  Button[PlayerAvatar].DeselectColG:= DesCol.G;
  Button[PlayerAvatar].DeselectColB:= DesCol.B;

  SelectsS[PlayerColor].SBGDColR := DesCol.R;
  SelectsS[PlayerColor].SBGDColG:= DesCol.G;
  SelectsS[PlayerColor].SBGDColB:= DesCol.B;

  SelectsS[PlayerSelectLevel].SBGDColR := DesCol.R;
  SelectsS[PlayerSelectLevel].SBGDColG:= DesCol.G;
  SelectsS[PlayerSelectLevel].SBGDColB:= DesCol.B;

  Button[PlayerAvatarButton[0]].Texture.ColR := DesCol.R;
  Button[PlayerAvatarButton[0]].Texture.ColG := DesCol.G;
  Button[PlayerAvatarButton[0]].Texture.ColB := DesCol.B;

  if (PlayerAvatars[PlayerIndex] = 0) then
  begin
    Statics[PlayerCurrentAvatar[PlayerIndex]].Texture.ColR := DesCol.R;
    Statics[PlayerCurrentAvatar[PlayerIndex]].Texture.ColG := DesCol.G;
    Statics[PlayerCurrentAvatar[PlayerIndex]].Texture.ColB := DesCol.B;
  end;

  SelectsS[PlayerColor].SetSelect(false);
  SelectsS[PlayerSelectLevel].SetSelect(false);
  Button[PlayerName].SetSelect(false);
  Button[PlayerAvatar].SetSelect(false);

  Num[PlayerIndex] := K;
  Ini.PlayerColor[PlayerIndex] := K;
end;

constructor TScreenName.Create;
var
  I: integer;
begin
  inherited Create;

  LoadFromTheme(Theme.Name);

  Theme.Name.SelectPlayersCount.oneItemOnly := true;
  Theme.Name.SelectPlayersCount.showArrows := true;
  PlayersCount := AddSelectSlide(Theme.Name.SelectPlayersCount, CountIndex, IPlayers);

  for I := 0 to UIni.IMaxPlayerCount -1 do
  begin
    PlayerCurrentAvatar[I] := AddStaticRectangle(Theme.Name.PlayerSelectAvatar[I]);
    PlayerCurrent[I] := AddStatic(Theme.Name.PlayerSelect[I]);
    PlayerCurrentText[I] := AddText(Theme.Name.PlayerSelectText[I]);
  end;

  PlayerSelect := AddButton(Theme.Name.PlayerSelectCurrent);

  PlayerAvatar := AddButton(Theme.Name.PlayerButtonAvatar);
  PlayerAvatarIID := High(Interactions);
  if not Theme.Name.PlayerScrollAvatar.Show then
  begin
    // theme without avatar pictures: the players only have their colour
    Button[PlayerAvatar].Visible := false;
    Button[PlayerAvatar].Selectable := false;
  end;

  PlayerName := AddButton(Theme.Name.PlayerButtonName);
  Button[PlayerName].Text[0].Writable := true;

  Theme.Name.SelectPlayerColor.oneItemOnly := true;
  Theme.Name.SelectPlayerColor.showArrows := true;
  PlayerColor := AddSelectSlide(Theme.Name.SelectPlayerColor, ColorIndex, IPlayerColorTranslated);

  Theme.Name.SelectPlayerLevel.oneItemOnly := true;
  Theme.Name.SelectPlayerLevel.showArrows := true;
  PlayerSelectLevel := AddSelectSlide(Theme.Name.SelectPlayerLevel, LevelIndex, IDifficultyTranslated);

  isScrolling := false;

  GenerateAvatars();

  NumVisibleAvatars := Theme.Name.PlayerScrollAvatar.NumAvatars;
  DistanceVisibleAvatars := Theme.Name.PlayerScrollAvatar.DistanceAvatars;

  Interaction := 0;
end;

procedure TScreenName.SetPlayerAvatar(Player: integer);
var
  Col: TRGB;
begin

  if (PlayerAvatars[Player] = 0) then
  begin
    Statics[PlayerCurrentAvatar[Player]].Texture.Free;
    Statics[PlayerCurrentAvatar[Player]].Texture := NoAvatarTexture[Player + 1].Clone;

    Col := GetPlayerColor(Num[Player]);

    Statics[PlayerCurrentAvatar[Player]].Texture.ColR := Col.R;
    Statics[PlayerCurrentAvatar[Player]].Texture.ColG := Col.G;
    Statics[PlayerCurrentAvatar[Player]].Texture.ColB := Col.B;
  end
  else
  begin
    Statics[PlayerCurrentAvatar[Player]].Texture.Free;
    Statics[PlayerCurrentAvatar[Player]].Texture := Button[PlayerAvatarButton[PlayerAvatars[Player]]].Texture.Clone;
  end;

  Statics[PlayerCurrentAvatar[Player]].Texture.X := Theme.Name.PlayerSelectAvatar[Player].X;
  Statics[PlayerCurrentAvatar[Player]].Texture.Y := Theme.Name.PlayerSelectAvatar[Player].Y;
  Statics[PlayerCurrentAvatar[Player]].Texture.W := Theme.Name.PlayerSelectAvatar[Player].W;
  Statics[PlayerCurrentAvatar[Player]].Texture.H := Theme.Name.PlayerSelectAvatar[Player].H;
  Statics[PlayerCurrentAvatar[Player]].Texture.Z := Theme.Name.PlayerSelectAvatar[Player].Z;

  Statics[PlayerCurrentAvatar[Player]].Texture.Int := 1;

end;

procedure TScreenName.OnShow;
var
  I: integer;
begin
  inherited;

  // cards come in again
  CardsOpened := 0;
  CardAnimW := 0;

  Ini.ReloadNames;
  CountIndex := Ini.Players;

  for I := 0 to UIni.IMaxPlayerCount-1 do
  begin
    PlayerNames[I] := Ini.Name[I];
    PlayerLevel[I] := Ini.PlayerLevel[I];
    PlayerAvatars[I] := GetArrayIndex(AvatarsMD5, Ini.PlayerAvatar[I]);
    // if it is -1 then the current saved md5 does not exist anymore (file has changed or was deleted entirely)
    // setting it to 0 just resets it to the colorized default avatar
    if (PlayerAvatars[I] = -1) then
    begin
      PlayerAvatars[I] := 0;
    end;
  end;

  AvatarTarget := PlayerAvatars[PlayerIndex];
  AvatarCurrent := AvatarTarget;

  RefreshPlayers;

  // list players
  for I := 1 to PlayersPlay do
  begin
    Text[PlayerCurrentText[I - 1]].Text := Ini.Name[I - 1];
    SetPlayerAvatar(I - 1);
  end;

  PlayerColorButton(Num[PlayerIndex]);

  SelectsS[PlayersCount].SetSelectOpt(CountIndex);

  Button[PlayerName].Text[0].Text := PlayerNames[PlayerIndex];

  isScrolling := false;

  Interaction := 0;

  if not Help.SetHelpID(ID) then
    Log.LogWarn('No Entry for Help-ID ' + ID, 'ScreenName');
end;

procedure TScreenName.SetAvatarScroll;
var
  B:        integer;
  Angle:    real;
  Pos:      real;
  VS:       integer;
  Padding:  real;
  X:        real;
  Factor:   real;
begin
  if not Theme.Name.PlayerScrollAvatar.Show then
  begin
    for B := 0 to High(PlayerAvatarButton) do
      if (PlayerAvatarButton[B] > 0) then // 0: slot of an avatar that could not be loaded
        Button[PlayerAvatarButton[B]].Visible := false;
    Exit;
  end;


  VS := Length(AvatarsList);

  case NumVisibleAvatars of
    1: begin
        Factor := 0;
       end;
    3: begin
        Factor := 1;
       end;
    5: begin
        Factor := 1.5;
       end;
   end;

  // Update positions of all avatars
  for B := PlayerAvatarButton[0] to PlayerAvatarButton[High(AvatarsList)] do
  begin
    Button[B].Visible := true; // adjust visibility

    // Pos is the distance to the centered avatar in the range [-VS/2..+VS/2]
    Pos := (B - PlayerAvatarButton[0] - AvatarCurrent);
    if (Pos < -VS/2) then
      Pos := Pos + VS
    else if (Pos > VS/2) then
      Pos := Pos - VS;

    // Avoid overlapping of the front avatars.
    // Use an alternate position for the others.
    if (Abs(Pos) < (NumVisibleAvatars/2)) then
    begin
      if (NumVisibleAvatars > 1) then
      begin
        Angle := Pi * (Pos / Min(VS, NumVisibleAvatars)); // Range: (-1/4*Pi .. +1/4*Pi)

        Button[B].H := Abs(Theme.Name.PlayerAvatar.H * cos(Angle*0.8));
        Button[B].W := Abs(Theme.Name.PlayerAvatar.W * cos(Angle*0.8));

        //Button[B].Reflectionspacing := 15 * Button[B].H/Theme.Song.Cover.H;
        Button[B].DeSelectReflectionspacing := 15 * Button[B].H/Theme.Name.PlayerAvatar.H;

        Padding := (Button[B].W - Theme.Name.PlayerAvatar.W)/2;
        X := Sin(Angle*1.3) * 0.9;

        Button[B].X := Theme.Name.PlayerAvatar.X + (Theme.Name.PlayerAvatar.W * Factor + DistanceVisibleAvatars) * X - Padding;
        Button[B].Y := (Theme.Name.PlayerAvatar.Y  + (Theme.Name.PlayerAvatar.H - Abs(Theme.Name.PlayerAvatar.H * cos(Angle))) * 0.5);
        Button[B].Z := 0.95 - Abs(Pos) * 0.01;

        // flat themes can turn the mirror effect off
        Button[B].Reflection := Theme.Name.PlayerScrollAvatar.Reflection;
        Button[B].Reflectionspacing := 2;

        if (B <> PlayerAvatarButton[PlayerAvatars[PlayerIndex]]) then
        begin
          Button[B].Texture.Int := 0.7;
        end
        else
        begin
          Button[B].Texture.Int := 1;
        end;
      end
      else
      begin
        Button[B].X := Theme.Name.PlayerAvatar.X;
        Button[B].Y := Theme.Name.PlayerAvatar.Y;

        AvatarCurrent := AvatarTarget;
        
        isScrolling := false;
      end

    end
    else
    begin
      Button[B].Visible := false;
    end;

  end;

end;

procedure TScreenName.SelectNext;
var
  VS:   integer;
begin

  VS := Length(AvatarsList);

  if VS > 0 then
  begin

    if (not isScrolling) and (VS > 0) then
    begin
      isScrolling := true;
    end;

    AvatarTarget := AvatarTarget + 1;

    // try to keep all at the beginning
    if AvatarTarget > VS-1 then
    begin
      AvatarTarget := AvatarTarget - VS;
      AvatarCurrent := AvatarCurrent - VS;
    end;
  end;

end;

procedure TScreenName.SelectPrev;
var
  VS:   integer;
begin

  VS := Length(AvatarsList);

  if VS > 0 then
  begin
    if (not isScrolling) and (VS > 0) then
    begin
      isScrolling := true;
    end;

    AvatarTarget := AvatarTarget - 1;

    // try to keep all at the beginning
    if AvatarTarget < 0 then
    begin
      AvatarTarget := AvatarTarget + VS;
      AvatarCurrent := AvatarCurrent + VS;
    end;
  end;

end;

function TScreenName.Draw: boolean;
var
  dx: real;
  dt: real;
  I: integer;
begin
  //inherited Draw;
  //heres a little Hack, that causes the Statics
  //are Drawn after the Buttons because of some Blending Problems.
  //This should cause no Problems because all Buttons on this screen
  //Has Z Position.
  DrawBG;

  if Ini.ReloadNames then
  begin
    OnShow;
  end;

  if isScrolling then
  begin
    dx := AvatarTarget - AvatarCurrent;
    dt := TimeSkip * 7;

    if dt > 1 then
      dt := 1;

    AvatarCurrent := AvatarCurrent + dx*dt;

    if SameValue(AvatarCurrent, AvatarTarget, 0.002) and (Length(AvatarsList) > 0) then
    begin
      isScrolling := false;
      AvatarCurrent := AvatarTarget;
    end;
  end;

  SetAvatarScroll;

  // set current name = name in list
  Text[PlayerCurrentText[PlayerIndex]].Text := Button[PlayerName].Text[0].Text;

  if Theme.Name.Cards.Enabled then
    DrawCards;

  //Instead of Draw FG Procedure:
  //We draw Buttons for our own
  for I := 0 to High(Button) do
    Button[I].Draw;

  // SelectsS
  for I := 0 to High(SelectsS) do
    SelectsS[I].Draw;

  // Statics
  for I := 0 to High(Statics) do
    Statics[I].Draw;

  // and texts
  for I := 0 to High(Text) do
    Text[I].Draw;

  Result := true;
end;

end.
