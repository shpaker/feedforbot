package core

import (
	"fmt"
	"strconv"

	pongo2 "github.com/flosch/pongo2/v6"
	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

type TelegramTarget struct {
	bot                      *tgbotapi.BotAPI
	chat                     string
	template                 pongo2.Template
	disable_notification     bool
	disable_web_page_preview bool
}

func NewTelegramTarget(token string, chat string, template pongo2.Template, disable_notification bool, disable_web_page_preview bool) (*TelegramTarget, error) {
	bot, err := tgbotapi.NewBotAPI(token)
	if err != nil {
		return nil, fmt.Errorf("failed to create telegram bot: %w", err)
	}
	return &TelegramTarget{
		bot:                      bot,
		chat:                     chat,
		template:                 template,
		disable_notification:     disable_notification,
		disable_web_page_preview: disable_web_page_preview,
	}, nil
}

func (t *TelegramTarget) makeMessage(chatID string, message string) tgbotapi.MessageConfig {
	chatIDInt, err := strconv.Atoi(chatID)
	if err == nil {
		return tgbotapi.NewMessage(int64(chatIDInt), message)
	}
	return tgbotapi.NewMessageToChannel(chatID, message)
}

func (t *TelegramTarget) Send(update Update) *error {
	text, err := t.template.Execute(update.GetTemplateContext())
	if err != nil {
		return &err
	}
	message := t.makeMessage(t.chat, text)
	message.ParseMode = "HTML"

	_, err = t.bot.Send(message)
	if err != nil {
		return &err
	}

	return nil
}
