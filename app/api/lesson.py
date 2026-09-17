from fastapi import APIRouter, HTTPException, UploadFile, File
from app.schemas.input import TextbookInput
from app.schemas.output import LessonPlanOutput, TeachingDesign
from app.agents.graph import build_graph
from app.tools import parse_textbook_bytes

router = APIRouter(prefix="/api", tags=["教案生成"])


@router.post("/parse-file", summary="上传课本文件并解析为文本")
async def parse_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        text = parse_textbook_bytes(content, file.filename)
        if not text.strip():
            raise HTTPException(status_code=400, detail="未从文件中解析到任何文本内容")
        return {"filename": file.filename, "content": text}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件解析失败: {str(e)}")


@router.post("/generate", response_model=LessonPlanOutput, summary="生成教学活动设计")
def generate_lesson_plan(input_data: TextbookInput):
    if not input_data.textbook_content or not input_data.textbook_content.strip():
        raise HTTPException(status_code=400, detail="课本内容不能为空，请输入文本或上传文件")

    try:
        graph = build_graph()
        result = graph.invoke({"textbook_input": input_data})

        design = TeachingDesign(
            pre_class_prep=[],
            teaching_process=result["teaching_stages"],
            blackboard_design=result["blackboard_design"],
            homework=result["homework"],
            teaching_reflection=result.get("teaching_reflection"),
        )

        output = LessonPlanOutput(
            lesson_title=result["extracted_textbook"].lesson_title,
            teaching_objectives=result["teaching_objectives"],
            key_difficult_points=result["key_difficult_points"],
            teaching_design=design,
        )
        return output
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"教案生成失败: {str(e)}")


@router.get("/generate/info", summary="获取生成流程信息")
def generate_info():
    return {
        "stages": [
            "textbook_parser - 课本解析与知识点抽取",
            "objective - 教学目标生成",
            "key_difficult - 重点难点分析",
            "process - 教学过程设计",
            "reviewer - 教案审核（含反馈修改）",
        ],
        "max_revisions": 2,
    }
