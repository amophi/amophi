# 그림과 글꼴의 출처

이 저장소는 [github.com/amophi](https://github.com/amophi) 프로필에 보이는 README 입니다.

## 그림

| 그림 | 출처 |
| --- | --- |
| `tools/pictures/show_*.jpg`, `tools/pictures/work_sv.jpg`, `assets/pictures/clip-*.webp` | 영화 장면은 Blender Foundation 의 〈Tears of Steel〉입니다. [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/), (CC) Blender Foundation, [mango.blender.org](https://mango.blender.org). 그 위의 오버레이는 SoundVisualizer for Android v1.8.0 이 에뮬레이터에서 실제로 그린 화면을 찍은 것입니다. |
| `tools/pictures/work_pildong.jpg` | 〈어서오세요 필동 편의점에!〉의 실제 게임 화면([itch.io](https://yj720.itch.io/the-ultimate-hardcore-convenience-store)에 올린 그림). |
| `tools/pictures/work_highschool.jpg` | 〈하이스쿨 하이스코어〉의 실제 게임 화면. |
| `tools/pictures/work_dead0.jpg` | 〈D(ead)0〉의 실제 게임 화면. |

`assets/` 의 SVG 는 `tools/build.py` 가 위 그림과 `tools/text.json` 의 문구로 만듭니다.

## 글꼴

글자는 [Pretendard](https://github.com/orioncactus/pretendard)(SIL Open Font License 1.1)의 글자 도형을 그림 안에 넣은 것입니다. 글꼴 파일은 저장소에 들어 있지 않습니다.

## 다시 만들기

```
pip install fonttools
python tools/build.py
```

Pretendard OTF 파일이 있는 폴더를 `PRETENDARD_DIR` 환경 변수로 알려 주거나 `tools/fonts/` 에 두면 됩니다. Windows 에 설치돼 있으면 그대로 찾습니다.
