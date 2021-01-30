from discord.ext import commands  # Bot Commands Frameworkのインポート
from .modules.grouping import MakeTeam
from .modules.readjson import ReadJson
from logging import getLogger
from .modules.coyote import Coyote

import asyncio
import random
import re

logger = getLogger(__name__)

# コグとして用いるクラスを定義。
class GameCog(commands.Cog, name='ゲーム用'):
    """
    ゲーム機能のカテゴリ。
    """
    MAX_TIME = 10
    DEFAULT_TIME = 2

    # GameCogクラスのコンストラクタ。Botを受取り、インスタンス変数として保持。
    def __init__(self, bot):
        self.bot = bot
        self.coyoteGames = Coyote()

    # ワードウルフ機能
    @commands.command(aliases=['word','ww'], description='ワードウルフ機能(少数派のワードを与えられた人を当てるゲーム)')
    async def wordWolf(self, ctx, answer_minutes=None):
        """
        コマンド実行者が参加しているボイスチャンネルでワードウルフ始めます（BOTからDMが来ますがびっくりしないでください）
        引数(answer_minutes)として投票開始までの時間（3などの正数。単位は「分」）を与えることができます。デフォルトは2分です。
        3人増えるごとにワードウルフは増加します(3−5人→ワードウルフは1人、6−8人→ワードウルフは2人)
        """
        make_team = MakeTeam()
        make_team.my_connected_vc_only_flg = True
        await make_team.get_members(ctx)

        if make_team.mem_len < 3:
            msg = f'ワードウルフを楽しむには3人以上のメンバーが必要です(現在、{make_team.mem_len}人しかいません)'
            await ctx.send(msg)
            return

        if answer_minutes is None:
            answer_minutes = self.DEFAULT_TIME
        elif answer_minutes.isdecimal():
            answer_minutes = int(answer_minutes)
        else:
            answer_minutes = self.DEFAULT_TIME

        if answer_minutes > self.MAX_TIME:
            msg = f'ワードウルフはそんなに長い時間するものではないです(現在、{answer_minutes}分を指定しています。{self.MAX_TIME}分以内にして下さい)'
            await ctx.send(msg)
            return

        # ファイルを読み込み、ワードウルフ用のデータを作成
        read_json = ReadJson()
        read_json.readJson()

        #　お題の選定
        choiced_item = random.choice(read_json.list)
        odai = read_json.dict[choiced_item]
        citizen_odai, wolf_odai = random.sample(odai, 2)

        # ワードウルフの数設定
        wolf_numbers = make_team.mem_len // 3
        msg =   f'ワードウルフを始めます！　この中に、**{wolf_numbers}人のワードウルフ**が紛れ込んでいます(本人も知りません！)。\n'\
                f'DMでお題が配られますが、**ワードウルフだけは別のお題**が配られます(お題は2種類あります)。会話の中で不審な言動を察知し、みごとに'\
                f'投票でワードウルフを当てることができたら、市民の勝ち。**間違えて「市民をワードウルフ」だと示してしまった場合、ワードウルフの勝ち**です！！\n'\
                f'DMに送られたお題を確認し、**{answer_minutes}分話し合いののち、投票を実施**してください！！　今から開始します！'
        await ctx.send(msg)

        # メンバーをシャッフル
        random.shuffle(make_team.vc_members)
        netabare_msg = f'**ワードウルフのお題は||「{wolf_odai}」||**でした！\nワードウルフは'

        # それぞれに役割をDMで送信
        for player in make_team.vc_members:
            if wolf_numbers > 0:
                player_odai = wolf_odai
                wolf_numbers = wolf_numbers - 1
                netabare_msg += f'||{player.display_name}||さん '
            else:
                player_odai = citizen_odai
            dm = await player.create_dm()
            await dm.send(f'{player.mention}さんのワードは**「{player_odai}」**です！')

        netabare_msg += 'でした！　お疲れ様でした！'

        voting_msg = '投票の時間が近づいてきました。下記のメッセージで投票をお願いします。\n'\
                    '`/poll 誰がワードウルフ？'
        for player in make_team.vc_members:
            voting_msg += f' {player.display_name}'
        voting_msg += '`'

        # 投票のお願いメッセージを作成し、チャンネルに貼り付け
        voting_time = answer_minutes * 50
        await self.delayedMessage(ctx, voting_msg, voting_time)

        # ワードウルフのネタバレメッセージを作成し、チャンネルに貼り付け
        await self.delayedMessage(ctx, netabare_msg, (answer_minutes * 60) - voting_time)

    # NGワードゲーム機能
    @commands.command(aliases=['ngword','ngw','ngwg','ngg'], description='NGワードゲーム機能(禁止された言葉を喋ってはいけないゲーム)')
    async def ngWordGame(self, ctx, answer_minutes=None):
        """
        コマンド実行者が参加しているボイスチャンネルでNGワードゲームを始めます（BOTからDMが来ますがびっくりしないでください）
        引数(answer_minutes)として終了までの時間（3などの正数。単位は「分」）を与えることができます。デフォルトは2分です。
        """
        make_team = MakeTeam()
        make_team.my_connected_vc_only_flg = True
        await make_team.get_members(ctx)

        if make_team.mem_len < 2:
            msg = f'NGワードゲームを楽しむには2人以上のメンバーが必要です(現在、{make_team.mem_len}人しかいません)'
            await ctx.send(msg)
            return

        if answer_minutes is None:
            answer_minutes = self.DEFAULT_TIME
        elif answer_minutes.isdecimal():
            answer_minutes = int(answer_minutes)
        else:
            answer_minutes = self.DEFAULT_TIME

        if answer_minutes > self.MAX_TIME:
            msg = f'NGワードゲームはそんなに長い時間するものではないです(現在、{answer_minutes}分を指定しています。{self.MAX_TIME}分以内にして下さい)'
            await ctx.send(msg)
            return

        # ファイルを読み込み、NGワードゲーム用のデータを作成(ワードウルフの語彙を流用)
        read_json = ReadJson()
        read_json.readJson()

        msg =   f'NGワードゲームを始めます！　DMでそれぞれのNGワードを配りました！(**自分のNGワードのみ分かりません**)\n'\
                f'これから**雑談し、誰かがNGワードを口走ったら、「ドーン！！！」と指摘**してください。すぐさまNGワードが妥当か話し合いください(カッコがある場合は、どちらもNGワードです)。\n'\
                f'妥当な場合、NGワード発言者はお休みです。残った人で続けます。**最後のひとりになったら勝利**です！！\n'\
                f'まず、DMに送られたNGワードを確認し、相手が「NGワードを喋ってしまう」ようにトークしてください！**{answer_minutes}分で終了**です！　今から開始します！！'
        await ctx.send(msg)

        netabare_msg = ''
        # それぞれに役割をDMで送信
        for player in make_team.vc_members:
            #　お題の選定
            choiced_item = random.choice(read_json.list)
            odai = read_json.dict[choiced_item]
            ngword = random.choice(odai)
            netabare_msg += f'{player.display_name}さん:||{ngword}||, '

        for player in make_team.vc_members:
            dm = await player.create_dm()
            rpl_msg_del = f'{player.display_name}さん:(\|\|.+?\|\|, )'
            dm_msg = re.sub(rpl_msg_del, '', netabare_msg)
            dm_msg_open = dm_msg.replace('|', '').replace(', ', '\n')
            await dm.send(f'{player.mention}さん 他の人のNGワードはこちらです！\n{dm_msg_open}')

        netabare_msg = re.sub(', $', '', netabare_msg)

        # NGワードゲームのネタバレメッセージを作成し、チャンネルに貼り付け
        await self.delayedMessage(ctx, 'NGワードゲームのネタバレです！\nそれぞれ、' + netabare_msg + 'でした！', answer_minutes * 60)

    # コヨーテゲーム群
    @commands.group(aliases=['co','cog','cy','cg'], description='コヨーテするコマンド（サブコマンド必須）')
    async def coyoteGame(self, ctx):
        """
        コヨーテするコマンド群です。このコマンドだけでは実行できません。**半角スペースの後、続けて以下のサブコマンドを入力**ください。
        - コヨーテを始めたい場合は、`/cy start`または`/cy startAndAllMessage`を入力してください(startは説明が短く、startAndAllMessageは全てを説明します)。
        - コヨーテ中に、「コヨーテ！」をしたい場合は、`/cy coyote`を入力してください。
        - コヨーテ中に、次の回を始めたい場合は、`/cy deal`を入力してください。
        - コヨーテ中に、現在の状況を確認したい場合は、`/cy description`を入力してください。
        - コヨーテ中に、カードの能力を確認したい場合は、`/cy card`を入力してください。
        上級者向け機能
        - 説明を省略して、コヨーテを始める場合は、`/cy startAndNoMessage`を入力してください。
        - コヨーテ中に、ネタバレありで現在の状況を確認したい場合は、`/cy descriptionAll`を入力してください。
        - `/cy setDeckAndStart`で自分でデッキを作成できます。詳しくは`/help coyoteGame setDeckAndStart`でヘルプを確認ください。
        """
        # サブコマンドが指定されていない場合、メッセージを送信する。
        if ctx.invoked_subcommand is None:
            await ctx.send('このコマンドにはサブコマンドが必要です。')

    @coyoteGame.command(aliases=['s','st','ini','init'], description='コヨーテを始めるコマンド')
    async def start(self, ctx):
        """
        コヨーテを始めるコマンド（説明が程よいバージョン）
        - コヨーテのルールが分かる程度に省略しています。
        """
        await self.startCoyote(ctx)
        await self.coyoteLittleMessage(ctx)
        await self.dealAndMessage(ctx)

    @coyoteGame.command(aliases=['sa','sta','ina','inia'], description='コヨーテを始めるコマンド(全説明)')
    async def startAndAllMessage(self, ctx):
        """
        コヨーテを始めるコマンド（説明が多いバージョン）
        - 初心者はこちらのコマンドを実行してください。
        - コヨーテのルールが分かるように書いてありますが、一旦説明を見ながらゲームしてみると良いと思います。
        """
        await self.startCoyote(ctx)
        await self.coyoteAllMessage(ctx)
        await self.dealAndMessage(ctx)

    @coyoteGame.command(aliases=['sn','no','inn'], description='コヨーテを始めるコマンド(説明なし)')
    async def startAndNoMessage(self, ctx):
        """
        コヨーテを始めるコマンド（説明なし）
        - 上級者向けの機能です。ルールを説明されずとも把握している場合にのみ推奨します。
        """
        await self.startCoyote(ctx)
        msg = self.coyoteGames.create_description(True)
        await ctx.send(msg)
        await self.dealAndMessage(ctx)

    @coyoteGame.command(aliases=['sds','ss','set'], description='デッキを指定して、コヨーテを始めるコマンド(説明なし)')
    async def setDeckAndStart(self, ctx, *, deck=None):
        """
        デッキを指定してコヨーテを始めるコマンド（説明なし）
        - 上級者向けの機能です。ルールを説明されずとも把握している場合にのみ推奨します。
        - デッキを「,」(コンマ)で区切って指定します。二重引用符などは不要です。
        例：`/coyoteGame setDeckAndStart 20, 15, 15, 1, 1, 1, 1, 0, 0, 0, 0(Night), -5, -5, -10, *2(Chief), Max->0(Fox), ?(Cave), ?(Cave)`
        """
        make_team = MakeTeam()
        make_team.my_connected_vc_only_flg = True
        await make_team.get_members(ctx)

        if make_team.mem_len < 2:
            msg = f'コヨーテを楽しむには2人以上のメンバーが必要です(現在、{make_team.mem_len}人しかいません)'
            await ctx.send(msg)
            return
        if deck is None:
            msg = f'deckを指定してください。\n例：`/coyoteGame setDeckAndStart 20, 15, 15, 1, 1, 1, 1, 0, 0, 0, 0(Night), -5, -5, -10, *2(Chief), Max->0(Fox), ?(Cave), ?(Cave)`'
            await ctx.send(msg)
            return
        self.coyoteGames.set(make_team.vc_members)
        self.coyoteGames.setDeck(deck)
        self.coyoteGames.shuffle()
        msg = self.coyoteGames.create_description(True)
        await ctx.send(msg)
        await self.dealAndMessage(ctx)

    @coyoteGame.command(aliases=['c','co','cy','done'], description='コヨーテ！(前プレイヤーの数字がコヨーテの合計数を超えたと思った場合のコマンド)')
    async def coyote(self, ctx, you_id=None, number=0):
        """
        コヨーテ中に実行できる行動。「コヨーテ！」を行う
        - 「コヨーテ！」は前プレイヤーの宣言を疑う行動
        - 「前プレイヤーの宣言した数」が「実際にこの場にいるコヨーテの数よりも**大きい（オーバーした）**」と思う場合に実行してください
        引数は2つあり、どちらも必須です
        - 1.プレイヤーのID（@マークを打つと入力しやすい）
        - 2.前プレイヤーの宣言した数
        """
        if you_id is None:
            msg = '「コヨーテする相手」(@で指定)と「コヨーテを言われた人の数字」を指定してください。例：`/coyoteGame coyote @you 99`'
            await ctx.send(msg)
            return
        if number <= 0:
            msg = '「コヨーテを言われた人の数字」は「1以上の整数」(0もダメです)を指定してください。例：`/coyoteGame coyote @you 99`'
            await ctx.send(msg)
            return
        if await self.coyoteStartCheckNG(ctx):
            return
        # コヨーテ！した相手のメンバー情報を取得。取得できない場合はエラーを返す
        you_id = re.sub(r'[<@!>]', '', you_id)
        if you_id.isdecimal():
            you_id = int(you_id)
            you = ctx.guild.get_member(you_id)
        else:
            # IDから取得を試みる
            keys = [k for k, v in self.coyoteGames.members.items() if v.id == str(you_id).upper()]
            if len(keys) == 0:
                msg = '「コヨーテする相手」(@で指定するか、IDで指定(aなど))と「コヨーテを言われた人の数字」を指定してください。例：`/coyoteGame coyote @you 99`'
                await ctx.send(msg)
                return
            else:
                you = keys.pop()
        if you not in self.coyoteGames.members:
            msg = 'ゲームに存在する相手を選び、「コヨーテ！」してください(ゲームしている相手にはいません)。'
            await ctx.send(msg)
            return

        self.coyoteGames.coyote(ctx.author, you, number)
        await ctx.send(self.coyoteGames.description)

    @coyoteGame.command(aliases=['d','de','next'], description='ディール（次のターンを始める）')
    async def deal(self, ctx):
        """
        コヨーテ中に実行できる行動。カードを引いて、プレイヤーに配ります
        """
        if await self.coyoteStartCheckNG(ctx):
            return
        await self.dealAndMessage(ctx)

    @coyoteGame.command(aliases=['desc','setsumei'], description='状況説明(ターン数,HP,山札の数,捨て札の数,捨て札)')
    async def description(self, ctx):
        """
        状況を説明します。
        - ターン数、生き残っている人の数、それぞれのHP
        - 山札の数、捨て札の数、捨て札の中身
        """
        if await self.coyoteStartCheckNG(ctx, True):
            return
        msg = self.coyoteGames.create_description()
        await ctx.send(msg)

    @coyoteGame.command(aliases=['da','desca'], description='状況説明(全て/場のカードも分かる)')
    async def descriptionAll(self, ctx):
        """
        状況を全て説明します（場のカードもわかります）。
        - ターン数、生き残っている人の数、それぞれのHP
        - 山札の数、山札の中身、捨て札の数、捨て札の中身、場のカード
        """
        if await self.coyoteStartCheckNG(ctx, True):
            return
        msg = self.coyoteGames.create_description(True)
        await ctx.send(msg)

    @coyoteGame.command(aliases=['cards','ca'], description='カードの説明')
    async def card(self, ctx):
        """
        カードの能力を説明します。
        """
        msg = self.coyoteGames.create_description_card()
        await ctx.send(msg)

    async def startCoyote(self, ctx):
        make_team = MakeTeam()
        make_team.my_connected_vc_only_flg = True
        await make_team.get_members(ctx)

        if make_team.mem_len < 2:
            msg = f'コヨーテを楽しむには2人以上のメンバーが必要です(現在、{make_team.mem_len}人しかいません)'
            await ctx.send(msg)
            return
        self.coyoteGames.set(make_team.vc_members)
        self.coyoteGames.shuffle()

    async def dealAndMessage(self, ctx):
        self.coyoteGames.deal()
        dm_msg_all = ''
        # 全員分のメッセージを作成
        for player in self.coyoteGames.members:
            dm_msg_all += f'{player.display_name}さん: {self.coyoteGames.members[player].card}\n'
        # DM用メッセージを作成(送付する相手の名前が記載された行を削除)
        for player in self.coyoteGames.members:
            dm = await player.create_dm()
            rpl_msg_del = f'{player.display_name}さん:.+\n'
            dm_msg = re.sub(rpl_msg_del, '', dm_msg_all)
            await dm.send(f'{player.mention}さん 他の人のコヨーテカードはこちらです！\n{dm_msg}')
        await ctx.send(f'カードを配りました。DMをご確認ください。{self.coyoteGames.description}')
        self.coyoteGames.description = ''

    async def coyoteAllMessage(self, ctx):
        msg1 = 'コヨーテ：ゲーム目的\n**自分以外のプレイヤーのカード(DMに送られる)を見て、少なくとも何匹のコヨーテがこの場にいるかを推理します。**\n'\
            'もしも宣言した数だけ居なかったら......コヨーテに命を奪われてしまいます！ インディアン、嘘つかない。コヨーテだって、嘘が大キライなのです。\n'\
            'ライフは一人3ポイントあります。3回殺されたらゲームから退場します。\n'\
            'コヨーテの鳴き声（想像してね）が上手いプレイヤーから始めます。'
        await ctx.send(msg1)

        msg2 = '最初のプレイヤーはDMに送られる他の人のカードを見て、この場に「少なくとも」何匹のコヨーテがいるか(DMを見て数字を加算し)推理し、コヨーテの数を宣言します。\n'\
            '★宣言する数に上限はありませんが、**1以上の整数である必要**があります（つまり、0や負数はダメです）\n'\
            'ゲームは時計回りに進行(ボイスチャンネルを下に進むこと)します。\n'\
            '次のプレイヤーは次のふたつのうち、「どちらか」の行動をとってください。\n'\
            '1: 数字を上げる → 前プレイヤーの宣言した数が実際にこの場にいるコヨーテの数**以下（オーバー）していない**と思う場合、**前プレイヤーより大きな数**を宣言します。\n'\
            '2: 「コヨーテ！」→ 前プレイヤーの宣言を疑います。つまり、前プレイヤーの宣言した数が実際にこの場にいるコヨーテの数よりも**大きい（オーバーした）**と思う場合、**「コヨーテ！」**と宣言します\n'\
            '2の場合、例：`/coyoteGame coyote @you 99`のように(`@you`はidでもOK)**Discordに書き込んで**ください！（Botが結果を判定します！）\n'\
            '**誰かが「コヨーテ！」と宣言するまで**、時計回りで順々に交代しながら宣言する数字を上げていきます\n'
        await ctx.send(msg2)

        msg3 = '「コヨーテ！」と宣言された場合、直前のプレイヤーが宣言した数が当たっていたかどうか判定します。\n'\
            '★前述の通り、Botが計算します（例：`/coyoteGame coyote @you 99`のように書き込んでくださいね）\n'\
            'まず基本カードを集計したあと、特殊カード分を計算します。\n'\
            '「コヨーテ！」を**宣言された数がコヨーテの合計数をオーバー**していた場合、**「コヨーテ！」を宣言した人**の勝ち（数値を宣言した人の負け）\n'\
            '「コヨーテ！」を**宣言された数がコヨーテの合計数以下**の場合、**数値を宣言**した人の勝ち（「コヨーテ！」を宣言した人の負け）\n'\
            '負けたプレイヤーはダメージを受けます（ライフが減ります）。\n'\
            '使ったカードを捨て札にして、次の回を始めます（**今回負けた人から開始**します）。\n'\
            '次の回を始めるには、`/coyoteGame deal`をDiscordに書き込んでください。\n'\
            '負けたプレイヤーがその回を最後に**ゲームから脱落した場合、その回の勝者から**次の回を始めます。\n'\
            'ライフが0になったプレイヤーはゲームから脱落します。最後まで生き残ったプレイヤーが勝利です。\n'\
            'なお、コヨーテは絶賛販売中です(1,800円くらい)。気に入った方はぜひ買って遊んでみてください（このBotは許可を得て作成したものではありません）。販売:合同会社ニューゲームズオーダー, 作者:Spartaco Albertarelli, 画:TANSANFABRIK\n'\
            'サイト: <http://www.newgamesorder.jp/games/coyote>'
        await ctx.send(msg3)

        msg4 = self.coyoteGames.create_description(True)
        await ctx.send(msg4)
        card_msg = self.coyoteGames.create_description_card()
        await ctx.send(card_msg)

    async def coyoteLittleMessage(self, ctx):
        msg = 'コヨーテ：ゲーム目的\n**自分以外のプレイヤーのカード(DMに送られる)を見て、少なくとも何匹のコヨーテがこの場にいるかを推理します。**\n'\
            'もしも宣言した数だけ居なかったら......コヨーテに命を奪われてしまいます！ インディアン、嘘つかない。コヨーテだって、嘘が大キライなのです。\n'\
            'ライフは一人3ポイントあります。3回殺されたらゲームから退場します。\n'\
            '最初のプレイヤー:「少なくとも」何匹のコヨーテがいるか推理し、コヨーテの数を宣言(**1以上の整数**)します。\n'\
            'ゲームは時計回りに進行(ボイスチャンネルを下に進むこと)\n'\
            '次のプレイヤー：は次のふたつのうち、「どちらか」の行動をとってください。\n'\
            '1: 数字を上げる → 前プレイヤーの宣言した数が実際にこの場にいるコヨーテの数**以下（オーバー）していない**と思う場合、**前プレイヤーより大きな数**を宣言します。\n'\
            '2: 「コヨーテ！」→ 前プレイヤーの宣言を疑います。つまり、前プレイヤーの宣言した数が実際にこの場にいるコヨーテの数よりも**大きい（オーバーした）**と思う場合、**「コヨーテ！」**と宣言します\n'\
            '2の場合、例：`/coyoteGame coyote @you 99`のように(`@you`はidでもOK)**Discordに書き込んで**ください！（Botが結果を判定します！）\n'\
            '**誰かが「コヨーテ！」と宣言するまで**、時計回り(ボイスチャンネルを下に進む)で順々に交代しながら宣言する**数字を上げて**いきます\n'\
            '次の回を始めるには、`/coyoteGame deal`をDiscordに書き込んでください（**今回負けた人から開始**します）。\n'\
            '負けたプレイヤーがその回を最後に**ゲームから脱落した場合、その回の勝者から**次の回を始めます。\n'\
            'ライフが0になったプレイヤーはゲームから脱落します。最後まで生き残ったプレイヤーが勝利です。\n'\
            'なお、コヨーテは絶賛販売中です(1,800円くらい)。気に入った方はぜひ買って遊んでみてください（このBotは許可を得て作成したものではありません）。販売:合同会社ニューゲームズオーダー, 作者:Spartaco Albertarelli, 画:TANSANFABRIK\n'\
            'サイト: <http://www.newgamesorder.jp/games/coyote>'
        await ctx.send(msg)
        msg2 = self.coyoteGames.create_description(True)
        await ctx.send(msg2)
        card_msg = self.coyoteGames.create_description_card()
        await ctx.send(card_msg)

    async def coyoteStartCheckNG(self, ctx, desc=False):
        if self.coyoteGames is None or (len(self.coyoteGames.members) <= 1 and not desc):
            msg = 'コヨーテを始めてから実行できます。コヨーテを始めたい場合は、`/coyoteGame start`または`/coyoteGame startAndAllMessage`を入力してください。'
            await ctx.send(msg)
            return True
        # 終わった後に説明が見たい場合は許す
        elif len(self.coyoteGames.members) == 1 and desc:
            return False
        else:
            return False

    @wordWolf.error
    async def wordWolf_error(self, ctx, error):
        if isinstance(error, commands.CommandError):
            logger.error(error)
            await ctx.send(error)

    @ngWordGame.error
    async def ngWordGame_error(self, ctx, error):
        if isinstance(error, commands.CommandError):
            logger.error(error)
            await ctx.send(error)

    @coyoteGame.error
    async def coyoteGame_error(self, ctx, error):
        if isinstance(error, commands.CommandError):
            logger.error(error)
            await ctx.send(error)

    async def delayedMessage(self, ctx, messsage, delayed_seconds=None):
        await asyncio.sleep(delayed_seconds)
        await ctx.send(messsage)

def setup(bot):
    bot.add_cog(GameCog(bot)) # GameCogにBotを渡してインスタンス化し、Botにコグとして登録する
