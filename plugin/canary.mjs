// Ручной прогон канарейки — без запуска ДСХ.
//
// Запуск:  node .dsh/plugin-reglament/canary.mjs
// Выход: 0 — все ворота кусают; 1 — есть слепые (защиты нет, разбирайся).

import { проверитьBash, прогнатьКанарейку } from './canary.js';
import { запуститьПроцесс, запуститьХук } from './index.js';

const КОРЕНЬ = 'D:\\Program\\Body\\planapp_django(DSH)';
const НАСТРОЙКИ = {
  корень: КОРЕНЬ,
  python: 'python',
  bash: 'C:\\Program Files\\Git\\bin\\bash.exe',
};

const bash = проверитьBash({
  запуститьBash: (команда) =>
    запуститьПроцесс({
      команда: НАСТРОЙКИ.bash,
      аргументы: ['-c', команда],
      рабочаяПапка: КОРЕНЬ,
      payload: {},
    }),
});
console.log(bash.строка);

const итог = прогнатьКанарейку({
  корень: КОРЕНЬ,
  запустить: (описание) => запуститьХук({ ...НАСТРОЙКИ, ...описание }),
});
for (const строка of итог.строки) console.log(строка);

console.log(`канареек: ${итог.всего}, слепых: ${итог.слепых.length}`);
if (!bash.жив || итог.слепых.length) {
  console.log('ВОРОТА ОСЛЕПЛИ: защиты сейчас нет');
  process.exitCode = 1;
} else {
  console.log('все ворота кусают');
}
