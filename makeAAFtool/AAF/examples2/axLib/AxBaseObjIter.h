
#include <memory>
#include <deque>
#include "AxBaseObj.h"
#include "AxObject.h"
#include "AxProperty.h"
#include "AxPropertyValue.h"


// Minimal stub for AxBaseObjIterPrtcl
class AxBaseObjIterPrtcl {
public:
	virtual ~AxBaseObjIterPrtcl() {}
	virtual bool NextOne(std::unique_ptr<AxBaseObj>& ret) { return false; }
	virtual void Reset() {}
	virtual std::unique_ptr<AxBaseObjIterPrtcl> Clone() { return nullptr; }
};

// Minimal stub for missing template classes
template <typename T1, typename T2 = void, typename T3 = void>
class AxBaseObjIter : public AxBaseObjIterPrtcl {
public:
	AxBaseObjIter(T1) {}
	virtual ~AxBaseObjIter() {}
};

template <typename T>
class AxBaseSolitaryObjIter : public AxBaseObjIterPrtcl {
public:
	AxBaseSolitaryObjIter(T) {}
	virtual ~AxBaseSolitaryObjIter() {}
};

template <typename TypeDef>
class AxBaseArrayObjIter : public AxBaseObjIterPrtcl {
public:
	AxBaseArrayObjIter(TypeDef) {}
	virtual ~AxBaseArrayObjIter() {}
	virtual bool NextOne(std::unique_ptr<AxBaseObj>& ret) override { return false; }
	virtual void Reset() override {}
	virtual std::unique_ptr<AxBaseObjIterPrtcl> Clone() override { return nullptr; }
};

// Minimal stub for AxBaseObjRecIter
class AxBaseObjRecIter {
public:
	AxBaseObjRecIter(std::unique_ptr<AxBaseObjIterPrtcl> root) {}
	~AxBaseObjRecIter() {}
	void Push(std::unique_ptr<AxBaseObjIterPrtcl> iter) {}
	void Pop() {}
	AxBaseObjIterPrtcl& Top() { static AxBaseObjIterPrtcl dummy; return dummy; }
	bool Empty() { return true; }
	int Size() { return 0; }
	bool NextOne(std::unique_ptr<AxBaseObj>& objRet, int& level) { return false; }
	void PopStack() {}
	int GetLevel() { return 0; }
	void HandleObjectRecursion(AxObject& obj) {}
	void HandlePropertyRecursion(AxProperty& prop) {}
	void HandlePropertyValueRecursion(AxPropertyValue& propVal) {}
	void HandleRecordPropertyValueRecursion(void* recPair) {}
private:
	std::deque<std::unique_ptr<AxBaseObjIterPrtcl>> _deque;
};

// Minimal stub for AxBaseRecordObjIter
class AxBaseRecordObjIter : public AxBaseObjIterPrtcl {
public:
	AxBaseRecordObjIter(std::unique_ptr<void> axRecordIter) {}
	~AxBaseRecordObjIter() {}
	virtual bool NextOne(std::unique_ptr<AxBaseObj>& ret) { return false; }
	virtual void Reset() {}
	virtual std::unique_ptr<AxBaseObjIterPrtcl> Clone() { return nullptr; }
private:
	std::unique_ptr<void> _axRecordIter;
};
